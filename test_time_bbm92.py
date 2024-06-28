from qunetsim import Qubit
from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
import random
import matplotlib.pyplot as plt
import time

Logger.DISABLED = True
WAIT_TIME = 200
INTERCEPTION = False


# Define the p_eve values
P_EVE_VALUES = [0.1, 0.3, 0.5]
# Define the key sizes
KEY_SIZES = [128,256,512,1024]

# Basis Declaration
BASIS = ['Z', 'X']  # |0>|1> = Z-Basis; |+>|-> = X-Basis
##########################################################################


def entangle(host):     # 00 + 11
    q1 = Qubit(host)
    q2 = Qubit(host)
    q1.H()
    q1.cnot(q2)
    return q1, q2


def preparation(key_length):
    alice_basis = ""
    bob_basis = ""
    # sample_size = int(key_length * p_eve)
    for kl in range(key_length):
        alice_basis += random.choice(BASIS)
        bob_basis += random.choice(BASIS)
    # print("Alice basis: {}".format(alice_basis))
    # print("Bob basis: {}".format(bob_basis))
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

def alice(host, receiver, alice_basis, p_eve, key_length):
    alice_measured_bits = ""
    eavesdrop_indices = select_eavesdropping_indices(key_length, p_eve)
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
    ack_basis_alice = host.send_classical(receiver, (alice_basis, eavesdrop_indices), await_ack=True)
    if ack_basis_alice is not None:
        print("{}'s basis string successfully sent".format(host.host_id))
    # Receiving Basis from Bob
    basis_from_bob = host.get_classical(receiver, wait=WAIT_TIME)
    if basis_from_bob is not None:
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))

    # For Key
    alice_key = alice_key_string(alice_measured_bits, alice_basis, basis_from_bob[0].content,  eavesdrop_indices, key_length)

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


def bob(host, receiver, bob_basis, p_eve, key_length):
    bob_key = ""
    bob_measured_bits = ""
    # For Qubit and Basis
    for basis in bob_basis:
        q2 = host.get_qubit(receiver, wait=WAIT_TIME)
        if q2 is not None:
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
    bob_key = bob_key_string(bob_measured_bits, bob_basis, basis_from_alice, eavesdrop_indices, key_length)

    # For Broadcast Key
    alice_key = host.get_classical(receiver, wait=WAIT_TIME)
    if alice_key is not None:
        print("{}'s key got successfully by {}".format(receiver, host.host_id))
        if bob_key == alice_key[0].content:
            print("Same key from {}'s side".format(host.host_id))
    bob_brd_ack = host.send_classical(receiver, bob_key, await_ack=True)
    if bob_brd_ack is not None:
        print("{}'s key successfully sent to {}".format(host.host_id, receiver))


def main():
    results = {}

    

    for key_length in KEY_SIZES:
        results[key_length] = []
        for p_eve in P_EVE_VALUES:
            times = []
            for _ in range(2):
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

                if INTERCEPTION:
                    host_eve.q_relay_sniffing = True
                    host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

                alice_basis, bob_basis = preparation(key_length)

                start_time = time.time()
                t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, p_eve, key_length))
                t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis, p_eve, key_length))
                t1.join()
                t2.join()
                end_time = time.time()

                establishment_time = end_time - start_time
                times.append(establishment_time)

                network.stop(True)

            average_time = sum(times) / len(times)
            results[key_length].append((p_eve, average_time))
            print(f"Key length: {key_length}, p_eve: {p_eve}, Average Establishment Time: {average_time}")
    
    print(results)
    # Plot the results
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    for key_length, result in results.items():
        p_eve_values, avg_times = zip(*result)

        # Column Chart
        ax[0].bar(p_eve_values, avg_times, alpha=0.7, label=f'Key Length {key_length}')
        
        # Line Chart
        ax[1].plot(p_eve_values, avg_times, marker='o', linestyle='-', label=f'Key Length {key_length}')

    ax[0].set_xlabel('p_eve')
    ax[0].set_ylabel('Average Establishment Time (s)')
    ax[0].set_title('Establishment Time vs p_eve')
    ax[0].legend()

    ax[1].set_xlabel('p_eve')
    ax[1].set_ylabel('Average Establishment Time (s)')
    ax[1].set_title('Establishment Time vs p_eve')
    ax[1].legend()

    plt.tight_layout()
    plt.show()

    return results

if __name__ == '__main__':
    results = main()