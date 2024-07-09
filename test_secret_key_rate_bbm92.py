from qunetsim import Qubit
from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
import random
import matplotlib.pyplot as plt

Logger.DISABLED = True
KEY_LENGTH = 64
SAMPLE_SIZE = int(KEY_LENGTH / 4)
WAIT_TIME = 10
INTERCEPTION = False


# Basis Declaration
BASIS = ['Z', 'X']  # |0>|1> = Z-Basis; |+>|-> = X-Basis
##########################################################################


def entangle(host):     # 00 + 11
    q1 = Qubit(host)
    q2 = Qubit(host)
    q1.H()
    q1.cnot(q2)
    return q1, q2


def preparation():
    alice_basis = ""
    bob_basis = ""
    for kl in range(KEY_LENGTH):
        alice_basis += random.choice(BASIS)
        bob_basis += random.choice(BASIS)
    # print("Alice basis: {}".format(alice_basis))
    # print("Bob basis: {}".format(bob_basis))
    return alice_basis, bob_basis


def select_eavesdropping_indices(p_eve):
    return random.sample(range(KEY_LENGTH), int(p_eve * KEY_LENGTH))

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



def alice(host, receiver, alice_basis, p_eve):
    alice_measured_bits = ""
    eavesdrop_indices = select_eavesdropping_indices(p_eve)
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
    alice_key = alice_key_string(alice_measured_bits, alice_basis, basis_from_bob[0].content, eavesdrop_indices)

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


def bob(host, receiver, bob_basis):
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
    bob_key = bob_key_string(bob_measured_bits, bob_basis, basis_from_alice,eavesdrop_indices)

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
    results = []
    P_EVE_VALUES = [0.1,0.3,0.5]

    for p_eve in P_EVE_VALUES:
        key_rates = []
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

            if INTERCEPTION:
                host_eve.q_relay_sniffing = True
                host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

            alice_basis, bob_basis = preparation()

            t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, p_eve))
            t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis))
            t1.join()
            t2.join()

            # Calculate the secret key rate
            key_length = len(alice_key)
            secret_key_rate = key_length / KEY_LENGTH
            key_rates.append(secret_key_rate)

            network.stop(True)

        average_key_rate = sum(key_rates) / len(key_rates)
        results.append((p_eve, average_key_rate))
        print(f"p_eve: {p_eve}, Average Secret Key Rate: {average_key_rate}")

    # Plot the results
    p_eve_values, avg_key_rates = zip(*results)

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    # Column Chart
    ax[0].bar(p_eve_values, avg_key_rates, alpha=0.7)
    ax[0].set_xlabel('p_eve')
    ax[0].set_ylabel('Average Secret Key Rate')
    ax[0].set_title('Secret Key Rate vs p_eve')

    # Line Chart
    ax[1].plot(p_eve_values, avg_key_rates, marker='o', linestyle='-')
    ax[1].set_xlabel('p_eve')
    ax[1].set_ylabel('Average Secret Key Rate')
    ax[1].set_title('Secret Key Rate vs p_eve')

    plt.tight_layout()
    plt.show()

    return results

if __name__ == '__main__':
    results = main()