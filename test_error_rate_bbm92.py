from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
import random
import time
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st

Logger.DISABLED = True
KEY_LENGTH = 64
WAIT_TIME = 10
INTERCEPTION = True

f = open("error_rate_bbm92.txt", "a")

# Basis Declaration
BASIS = ['Z', 'X']  # |0>|1> = Z-Basis; |+>|-> = X-Basis

# Define the p_eve values
P_EVE_VALUES = [0.1, 0.3, 0.5]
# Define the error rates
ERROR_RATES = [0.05, 0.1, 0.15]

def entangle(host):
    q1 = Qubit(host)
    q2 = Qubit(host)
    q1.H()
    q1.cnot(q2)
    return q1, q2

def preparation(key_length):
    alice_basis = ""
    bob_basis = ""
    for _ in range(key_length):
        alice_basis += random.choice(BASIS)
        bob_basis += random.choice(BASIS)
    return alice_basis, bob_basis

def select_eavesdropping_indices(key_length, p_eve):
    return random.sample(range(key_length), int(p_eve * key_length))

def alice_key_string(alice_bits, alice_basis, bob_basis, eavesdrop_indices, key_length):
    alice_key = ""
    for i in range(key_length):
        if i not in eavesdrop_indices and alice_basis[i] == bob_basis[i]:
            alice_key += str(alice_bits[i])
    return alice_key

def bob_key_string(bob_bits, bob_basis, alice_basis, eavesdrop_indices, key_length):
    bob_key = ""
    for i in range(key_length):
        if i not in eavesdrop_indices and bob_basis[i] == alice_basis[i]:
            bob_key += str(bob_bits[i])
    return bob_key


def alice(host, receiver, alice_basis, p_eve, key_length, error_rate):
    alice_measured_bits = ""
    eavesdrop_indices = select_eavesdropping_indices(key_length,p_eve)
    # For Qubit and Basis
    for basis in alice_basis:
        q1, q2 = entangle(host)
        ack_arrived = host.send_qubit(receiver, q2, await_ack=False)
        if ack_arrived:
            if basis == 'Z':
                alice_measured_bits += str(q1.measure())
            if basis == 'X':
                q1.H()
                alice_measured_bits += str(q1.measure())
    print("Alice's measured bits: {}".format(alice_measured_bits))

    # Sending Basis to Bob
    ack_basis_alice = host.send_classical(receiver, (alice_basis,eavesdrop_indices), await_ack=True)
    if ack_basis_alice is not None:
        print("{}'s basis string successfully sent".format(host.host_id))
    # Receiving Basis from Bob
    basis_from_bob = host.get_classical(receiver, wait=WAIT_TIME)
    if basis_from_bob is not None:
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))

    global alice_key
    # For Key
    alice_key = alice_key_string(alice_measured_bits, alice_basis, basis_from_bob[0].content, eavesdrop_indices, KEY_LENGTH)

    # For Sending Key
    alice_brd_ack = host.send_classical(receiver, alice_key, await_ack=True)
    if alice_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))
    bob_key = host.get_classical(receiver, wait=WAIT_TIME)
    if bob_key is not None:
        print("{}'s got successfully by {}".format(receiver, host.host_id))
        if alice_key == bob_key[0].content:
            print("Same key from {}'s side".format(host.host_id))


def eve_sniffing_quantum(sender, receiver, qubit):
    qubit.measure(non_destructive=True)


def bob(host, receiver, bob_basis, error_rate):
    global bob_key
    bob_key = ""
    bob_measured_bits = ""
    # For Qubit and Basis
    for basis in bob_basis:
        q2 = host.get_qubit(receiver, wait=WAIT_TIME)
        if q2 is not None:
            if random.random() < error_rate: # simulate channel error
                q2.X() # bit flip error
            # Measuring Alice's qubit based on Bob's basis
            if basis == 'Z':  # Z-basis
                bob_measured_bits += str(q2.measure())
            if basis == 'X':  # X-basis
                q2.H()
                bob_measured_bits += str(q2.measure())
    print("Bob's measured bits: {}".format(bob_measured_bits))

    # Receiving Basis from Alice
    basis_from_alice, eavesdrop_indices = host.get_classical(receiver, wait=WAIT_TIME)[0].content
    if basis_from_alice is not None:
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))
    # Sending Basis to Alice
    ack_basis_bob = host.send_classical(receiver, bob_basis, await_ack=True)
    if ack_basis_bob is not None:
        print("{}'s basis string successfully sent".format(host.host_id))

    # For sample key indices
    bob_key = bob_key_string(bob_measured_bits, bob_basis, basis_from_alice,eavesdrop_indices, KEY_LENGTH)

    # For Broadcast Key
    alice_key = host.get_classical(receiver, wait=WAIT_TIME)
    if alice_key is not None:
        print("{}'s key got successfully by {}".format(receiver, host.host_id))
        if bob_key == alice_key[0].content:
            print("Same key from {}'s side".format(host.host_id))
    bob_brd_ack = host.send_classical(receiver, bob_key, await_ack=True)
    if bob_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))

def compute_confidence_interval(data, confidence=0.95):
    n = len(data)
    mean = np.mean(data)
    sem = st.sem(data)
    margin_of_error = sem * st.t.ppf((1 + confidence) / 2., n-1)
    return mean, mean - margin_of_error, mean + margin_of_error

def main():
    results = []
    for p_eve in P_EVE_VALUES:
        for error_rate in ERROR_RATES:
            key_rates=[]
            for _ in range(20):
                network = Network.get_instance()
                nodes = ['Alice', 'Eve', 'Bob']
                network.start(nodes)
                network.delay = 0.1

                host_alice = Host('Alice')
                host_alice.add_connection('Eve')
                host_alice.start()

                host_eve = Host('Eve')
                host_eve.add_connections(['Alice', 'Bob'])
                host_eve.start()

                host_bob = Host('Bob')
                host_bob.add_connection('Eve')
                host_bob.start()

                network.add_host(host_alice)
                network.add_host(host_bob)
                network.add_host(host_eve)
                network.start()

                if INTERCEPTION:
                    host_eve.q_relay_sniffing = True
                    host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

                alice_basis, bob_basis = preparation(KEY_LENGTH)

                t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, p_eve, KEY_LENGTH, error_rate))
                t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis, error_rate))
                t1.join()
                t2.join()

                key_length = len(alice_key)
                secret_key_rate = key_length/KEY_LENGTH

                key_rates.append(secret_key_rate)

                network.stop(True)
                time.sleep(2)

            mean, lower, upper = compute_confidence_interval(key_rates)
            print(mean,lower,upper, "Hwfj")

            results.append((error_rate, p_eve, mean, lower, upper))

            s = str(f"Error Rate: {error_rate}, p_eve: {p_eve}, Average Secret Key Rate: {mean}, 95% CI: [{lower}, {upper}]")
            f.write(s)

     # Plot the results
    error_rates, p_eve_values, avg_key_rates, lower_bounds, upper_bounds = zip(*results)
    error_rate_unique = sorted(set(error_rates))
    p_eve_unique = sorted(set(p_eve_values))

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    # Column Chart
    width = 0.2
    x = np.arange(len(error_rate_unique))
    for i, p_eve in enumerate(p_eve_unique):
        means = [avg for (er, pe, avg, lb, ub) in results if pe == p_eve]
        lows = [lb for (er, pe, avg, lb, ub) in results if pe == p_eve]
        highs = [ub for (er, pe, avg, lb, ub) in results if pe == p_eve]
        ax[0].bar(x + i * width, means, width, yerr=[np.subtract(means, lows), np.subtract(highs, means)], capsize=5, label=f'p_eve = {p_eve}', alpha=0.7)

    ax[0].set_xticks(x + width * (len(p_eve_unique) - 1) / 2)
    ax[0].set_xticklabels([str(er) for er in error_rate_unique])
    ax[0].set_xlabel('Error Rate')
    ax[0].set_ylabel('Average Secret Key Rate')
    ax[0].set_title('Secret Key Rate vs Error Rate')
    ax[0].legend()

    # Line Chart
    for p_eve in p_eve_unique:
        means = [avg for (er, pe, avg, lb, ub) in results if pe == p_eve]
        lows = [lb for (er, pe, avg, lb, ub) in results if pe == p_eve]
        highs = [ub for (er, pe, avg, lb, ub) in results if pe == p_eve]
        ax[1].errorbar(error_rate_unique, means, yerr=[np.subtract(means, lows), np.subtract(highs, means)], fmt='-o', label=f'p_eve = {p_eve}', capsize=5)

    ax[1].set_xlabel('Error Rate')
    ax[1].set_ylabel('Average Secret Key Rate')
    ax[1].set_title('Secret Key Rate vs Error Rate')
    ax[1].legend()

    plt.tight_layout()
    plt.show()

    f.close()

if __name__ == '__main__':
    main()