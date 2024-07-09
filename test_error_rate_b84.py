from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
import random
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as st
import time

Logger.DISABLED = True
WAIT_TIME = 200
KEY_LENGTH = 64
INTERCEPTION = False

# Define the error rates and p_eve values
ERROR_RATES = [0.05, 0.10, 0.15]
P_EVE_VALUES = [0.1, 0.3, 0.5]

f = open("error_rate_bb84.txt", "a")


# Basis Declaration
BASIS = ['Z', 'X']  # |0>|1> = Z-Basis; |+>|-> = X-Basis
#########################################################################


def q_bit(host, encode):
    q = Qubit(host)
    if encode == '+':
        q.H()
    if encode == '-':
        q.X()
        q.H()
    if encode == '0':
        q.I()
    if encode == '1':
        q.X()
    return q

def introduce_errors(qubit, error_rate):
    if random.random() < error_rate:
        qubit.X()  # Introduce an X error with the specified probability
    return qubit


def encoded_bases(alice_bits, alice_basis):
    alice_encoded = ""
    for i in range(0, len(alice_bits)):
        if alice_basis[i] == 'X':  # X-Basis
            if alice_bits[i] == '0':
                alice_encoded += '+'
            if alice_bits[i] == '1':
                alice_encoded += '-'
        if alice_basis[i] == 'Z':  # Z-Basis
            if alice_bits[i] == '0':
                alice_encoded += '0'
            if alice_bits[i] == '1':
                alice_encoded += '1'
    # print("Alice encoded: {}".format(alice_encoded))
    return alice_encoded


def preparation():
    alice_basis = ""
    bob_basis = ""
    alice_bits = ""
    for kl in range(KEY_LENGTH):
        alice_basis += random.choice(BASIS)
        bob_basis += random.choice(BASIS)
        alice_bits += str(random.getrandbits(1))
    alice_encoded = encoded_bases(alice_bits, alice_basis)
    return alice_basis, bob_basis, alice_bits, alice_encoded


def select_eavesdropping_indices(p_eve):
    return random.sample(range(KEY_LENGTH), int(p_eve)*KEY_LENGTH)


def alice_key_string(alice_bits, alice_basis, bob_basis, eavesdrop_indices):
    alice_key = ""
    for i in range(KEY_LENGTH):
        if i not in eavesdrop_indices and alice_basis[i] == bob_basis[i]:
            alice_key += str(alice_bits[i])
    return alice_key

def bob_key_string(bob_bits, bob_basis, alice_basis, eavesdrop_indices):
    bob_key = ""
    for i in range(KEY_LENGTH):
        if i not in eavesdrop_indices and bob_basis[i] == alice_basis[i]:
            bob_key += str(bob_bits[i])
    return bob_key



def alice(host, receiver, alice_basis, alice_bits, alice_encoded, p_eve, error_rate):
    eavesdropping_indices = select_eavesdropping_indices(p_eve)


    qubits_sent_count = 0

    # For Qubit and Basis
    for i, encode in enumerate(alice_encoded):
        q=q_bit(host,encode)
        q=introduce_errors(q,error_rate)
        _, ack = host.send_qubit(receiver, q, await_ack=True)
        if ack is not None:
            qubits_sent_count+=1
            # print("{}'s qubit {} successfully sent".format(host.host_id, i))
    ################################################################################
    
    print("Number of qubits sent by Alice: {}".format(qubits_sent_count))

    # Sending Basis to Bob
    ack_basis_alice = host.send_classical(receiver, (alice_basis,eavesdropping_indices), await_ack=True)
    if ack_basis_alice is not None:
        print("Ack basis alice", ack_basis_alice)
        print("{}'s basis string successfully sent".format(host.host_id))
    # Receiving Basis from Bob
    basis_from_bob = host.get_classical(receiver, wait=WAIT_TIME)
    if basis_from_bob is not None:
        print("Bob basis", basis_from_bob[0].content)
        # exit()
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))
        bob_basis = basis_from_bob[0].content

    else:
        print("Failed to receive basis from Bob.")
    ###############################################################################

    # For Key
    global alice_key
    alice_key = alice_key_string(alice_bits, alice_basis, bob_basis, eavesdropping_indices)
    #################################################################################

    # For Sending Key
    alice_brd_ack = host.send_classical(receiver, str(alice_key), await_ack=True)
    if alice_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))
    bob_key = host.get_classical(receiver, wait=WAIT_TIME)
    if bob_key is not None:
        # print("{}'s key got successfully by {}".format(receiver, host.host_id))
        if alice_key == bob_key[0].content:
            print("Same key from {}'s side".format(host.host_id))
        else:
            print("No")
    ################################################################################


def eve_sniffing_quantum(sender, receiver, qubit):
    qubit.measure(non_destructive=True)


def bob(host, receiver, bob_basis, p_eve, error_rate):
    bob_measured_bits = ""
    qubits_received_count = 0
    # For Qubit and Basis
    for i in range(0, len(bob_basis)):
        data = host.get_qubit(receiver, wait=WAIT_TIME)
        if data is not None:
            qubits_received_count+=1
            # print("{}'s qubit {} got successfully by {}".format(receiver, i, host.host_id))
        # Measuring Alice's qubit based on Bob's basis
        if bob_basis[i] == 'Z':  # Z-basis
            bob_measured_bits += str(data.measure())
        if bob_basis[i] == 'X':  # X-basis
            data.H()
            bob_measured_bits += str(data.measure())

    print("Number of qubits received by Bob: {}".format(qubits_received_count))
    print("Bob measured bit: {}".format(bob_measured_bits))
    ###############################################################################

    # Receiving Basis from Alice
    basis_from_alice = host.get_classical(receiver, wait=WAIT_TIME)
    if basis_from_alice is not None:
        alice_basis, eavesdropping_indices = basis_from_alice[0].content
        print('Alice_basis', alice_basis)
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))
    # Sending Basis to Alice
    ack_basis_bob = host.send_classical(receiver, bob_basis, await_ack=True)
    if ack_basis_bob is not None:
        print("{}'s basis string successfully sent".format(host.host_id))
    ################################################################################

    # For sample key indices
    bob_key = bob_key_string(bob_measured_bits, bob_basis, alice_basis, eavesdropping_indices)
    ##############################################################################

    # For Broadcast Key
    alice_key = host.get_classical(receiver, wait=WAIT_TIME)
    if alice_key is not None:
        print("{}'s key got successfully by {}".format(receiver, host.host_id))
        if bob_key == alice_key[0].content:
            print("Same key from {}'s side".format(host.host_id))
        else:
            print("No")
    bob_brd_ack = host.send_classical(receiver, str(bob_key), await_ack=True)
    if bob_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))
    ################################################################################



def compute_confidence_interval(data, confidence=0.95):
    n = len(data)
    mean = np.mean(data)
    sem = st.sem(data)
    margin_of_error = sem * st.t.ppf((1 + confidence) / 2., n-1)
    return mean, mean - margin_of_error, mean + margin_of_error

def main():

    results = []
    for error_rate in ERROR_RATES:
        for p_eve in P_EVE_VALUES:
            key_rates=[]
            for _ in range(20):
                # random.seed(42)
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
                host_bob.delay = 0.2
                host_bob.start()

                network.add_host(host_alice)
                network.add_host(host_eve)
                network.add_host(host_bob)
                network.start()
                
                alice_basis, bob_basis, alice_bits, alice_encoded = preparation()
                print("Alice bases: {}".format(alice_basis))
                print("Bob bases: {}".format(bob_basis))
                print("Alice bits: {}".format(alice_bits))
                print("Alice encoded: {}".format(alice_encoded))

                start_time = time.time()

                t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, alice_bits, alice_encoded, p_eve, error_rate))
                t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis, p_eve, error_rate))
                t1.join()
                t2.join()

                key_length = len(alice_key)

                secret_key_rate = key_length / KEY_LENGTH
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