# from qunetsim.components.host import Host
# from qunetsim.components.network import Network
# from qunetsim.objects import Qubit
# from qunetsim.objects import Logger
# import random
# import numpy as np
# import matplotlib.pyplot as plt
# import time

# Logger.DISABLED = True
# WAIT_TIME = 500
# INTERCEPTION = True


# # Basis Declaration
# BASIS = ['Z', 'X']  # |0>|1> = Z-Basis; |+>|-> = X-Basis
# ##########################################################################


# def q_bit(host, encode):
#     q = Qubit(host)
#     if encode == '+':
#         q.H()
#     if encode == '-':
#         q.X()
#         q.H()
#     if encode == '0':
#         q.I()
#     if encode == '1':
#         q.X()
#     return q


# def encoded_bases(alice_bits, alice_basis):
#     alice_encoded = ""
#     for i in range(0, len(alice_bits)):
#         if alice_basis[i] == 'X':  # X-Basis
#             if alice_bits[i] == '0':
#                 alice_encoded += '+'
#             if alice_bits[i] == '1':
#                 alice_encoded += '-'
#         if alice_basis[i] == 'Z':  # Z-Basis
#             if alice_bits[i] == '0':
#                 alice_encoded += '0'
#             if alice_bits[i] == '1':
#                 alice_encoded += '1'
#     # print("Alice encoded: {}".format(alice_encoded))
#     return alice_encoded



# def preparation(key_length):
#     alice_basis = ""
#     bob_basis = ""
#     alice_bits = ""
#     for kl in range(key_length):
#         alice_basis += random.choice(BASIS)
#         bob_basis += random.choice(BASIS)
#         alice_bits += str(random.getrandbits(1))
#     alice_encoded = encoded_bases(alice_bits, alice_basis)
#     return alice_basis, bob_basis, alice_bits, alice_encoded

# def select_eavesdropping_indices(p_eve, key_length):
#     return random.sample(range(key_length), int(p_eve * key_length))


# def alice_key_string(alice_bits, alice_basis, bob_basis, eavesdrop_indices):
#     alice_key = ""
#     for i in range(len(alice_bits)):
#         if i not in eavesdrop_indices and alice_basis[i] == bob_basis[i]:
#             alice_key += str(alice_bits[i])
#     return alice_key


# def bob_key_string(bob_bits, bob_basis, alice_basis, eavesdrop_indices):
#     bob_key = ""
#     for i in range(len(bob_bits)):
#         if i not in eavesdrop_indices and bob_basis[i] == alice_basis[i]:
#             bob_key += str(bob_bits[i])
#     return bob_key



# def alice(host, receiver, alice_basis, alice_bits, alice_encoded, p_eve):
#     eavesdrop_indices = select_eavesdropping_indices(p_eve, len(alice_bits))

#     print("Sample indices used for error detection {}".format(eavesdrop_indices))
#     # detection_percentage = (len(sample_indices)/KEY_LENGTH) * 100
#     # print("Percentage of qubits used for eavesdropping (error) detection: {:.2f}%".format(detection_percentage))

#     qubits_sent_count = 0

#     # For Qubit and Basis
#     for i, encode in enumerate(alice_encoded):
#         _, ack = host.send_qubit(receiver, q_bit(host,encode), await_ack=True)
#         if ack is not None:
#             qubits_sent_count+=1
#             # print("{}'s qubit {} successfully sent".format(host.host_id, i))
#     ################################################################################
    
#     print("Number of qubits sent by Alice: {}".format(qubits_sent_count))

#     # Sending Basis to Bob
#     ack_basis_alice = host.send_classical(receiver, (alice_basis,eavesdrop_indices), await_ack=True)
#     if ack_basis_alice is not None:
#         print("Ack basis alice", ack_basis_alice)
#         print("{}'s basis string successfully sent".format(host.host_id))
#     # Receiving Basis from Bob
#     basis_from_bob = host.get_classical(receiver, wait=WAIT_TIME)
#     if basis_from_bob is not None:
#         print("Bob basis", basis_from_bob[0].content)
#         # exit()
#         print("{}'s basis string got successfully by {}".format(receiver, host.host_id))
#         bob_basis = basis_from_bob[0].content

#     else:
#         print("Failed to receive basis from Bob.")
#     ###############################################################################

#     # For Key
#     global alice_key
#     alice_key = alice_key_string(alice_bits, alice_basis, bob_basis, eavesdrop_indices)
#     #################################################################################

#     # For Sending Key
#     alice_brd_ack = host.send_classical(receiver, str(alice_key), await_ack=True)
#     if alice_brd_ack is not None:
#         print("{}'s key successfully sent to {}".format(host.host_id, receiver))
#     bob_key = host.get_classical(receiver, wait=WAIT_TIME)
#     if bob_key is not None:
#         # print("{}'s key got successfully by {}".format(receiver, host.host_id))
#         if alice_key == bob_key[0].content:
#             print("Same key from {}'s side".format(host.host_id))
#         else:
#             print("No")
    
#     return alice_key
#     ################################################################################


# def eve_sniffing_quantum(sender, receiver, qubit):
#     qubit.measure(non_destructive=True)


# def bob(host, receiver, bob_basis, p_eve):
#     bob_measured_bits = ""
#     qubits_received_count = 0
#     # For Qubit and Basis
#     for i in range(0, len(bob_basis)):
#         data = host.get_qubit(receiver, wait=WAIT_TIME)
#         if data is not None:
#             qubits_received_count += 1
#         # Measuring Alice's qubit based on Bob's basis
#         if bob_basis[i] == 'Z':  # Z-basis
#             bob_measured_bits += str(data.measure())
#         if bob_basis[i] == 'X':  # X-basis
#             data.H()
#             bob_measured_bits += str(data.measure())

#     print("Number of qubits received by Bob: {}".format(qubits_received_count))
#     print("Bob measured bit: {}".format(bob_measured_bits))
#     ###############################################################################

#     # Receiving Basis from Alice
#     basis_from_alice = host.get_classical(receiver, wait=WAIT_TIME)
#     if basis_from_alice is not None:
#         alice_basis, eavesdrop_indices = basis_from_alice[0].content
#         print('Alice_basis', alice_basis)
#         print("These are the sample indices", eavesdrop_indices)
#         # print("Content from basis of alice" , basis_from_alice[0].content)
#         # exit()
#         print("{}'s basis string got successfully by {}".format(receiver, host.host_id))
#     # Sending Basis to Alice
#     # exit()
#     # exit()
#     ack_basis_bob = host.send_classical(receiver, bob_basis, await_ack=True)
#     if ack_basis_bob is not None:
#         print("{}'s basis string successfully sent".format(host.host_id))
#     ################################################################################

#     # For sample key indices
#     bob_key = bob_key_string(bob_measured_bits, bob_basis, alice_basis, eavesdrop_indices)
#     ##############################################################################

#     # For Broadcast Key
#     alice_key = host.get_classical(receiver, wait=WAIT_TIME)
#     if alice_key is not None:
#         print("{}'s key got successfully by {}".format(receiver, host.host_id))
#         if bob_key == alice_key[0].content:
#             print("Same key from {}'s side".format(host.host_id))
#         else:
#             print("No")
#     bob_brd_ack = host.send_classical(receiver, str(bob_key), await_ack=True)
#     if bob_brd_ack is not None:
#         print("{}'s key successfully sent to {}".format(host.host_id, receiver))
#     ################################################################################

#     # error_count = sum(1 for i in sample_indices if alice_basis[i] != bob_basis[i] or alice_bits[i] != bob_measured_bits[i])
#     # error_rate = error_count / len(sample_indices)
#     # print("Error Rate: {:.2%}".format(error_rate))

#     return bob_key,bob_measured_bits


# def main():

#     key_sizes = [128]
#     p_eve_values = [0.1]

#     final_key_lengths = {key_size: [] for key_size in key_sizes}

#     # {128: [62, 46, 31], 256: [121, 97, 67], 512: [223, 177, 124], 1024: [450, 348, 244]}

     
#     results = {key_size: {p_eve: [] for p_eve in p_eve_values} for key_size in key_sizes}
#     num_runs = 0
#     for _ in range(1):
#         num_runs+=1
#         for key_size in key_sizes:
#             for p_eve in p_eve_values:
                
#                 random.seed(42)
#                 network = Network.get_instance()
#                 nodes = ['Alice', 'Eve', 'Bob']
#                 network.start(nodes)
#                 network.delay = 0.1

#                 host_alice = Host('Alice')
#                 host_alice.add_connection('Eve')
#                 host_alice.start()

#                 host_eve = Host('Eve')
#                 host_eve.add_connections(['Alice', 'Bob'])
#                 host_eve.start()

#                 host_bob = Host('Bob')
#                 host_bob.add_connection('Eve')
#                 host_bob.delay = 0.2
#                 host_bob.start()

#                 network.add_host(host_alice)
#                 network.add_host(host_eve)
#                 network.add_host(host_bob)
#                 network.start()
                
#                 alice_basis, bob_basis, alice_bits, alice_encoded = preparation(key_size)
#                 print("Alice bases: {}".format(alice_basis))
#                 print("Bob bases: {}".format(bob_basis))
#                 print("Alice bits: {}".format(alice_bits))
#                 print("Alice encoded: {}".format(alice_encoded))

#                 if INTERCEPTION:
#                     host_eve.q_relay_sniffing = True
#                     host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

#                 start_time = time.time()

#                 t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, alice_bits, alice_encoded, p_eve,))
#                 t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis, p_eve ))
#                 t1.join()
#                 t2.join()

#                 end_time = time.time()

#                 key_length = len(alice_key)

#                 print(key_length)
#                 exit()
#                 elapsed_time = end_time - start_time
#                 results[key_size][p_eve].append(elapsed_time)
#                 final_key_lengths[key_size].append(key_length)


#                 network.stop(True)
#                 time.sleep(2)
    
#     print(final_key_lengths)
# #         print("runs completed : ", num_runs)
# # # Calculate average times
# #     average_times = {key_size: {p_eve: np.mean(results[key_size][p_eve]) for p_eve in p_eve_values} for key_size in key_sizes}
# #     print("Average Times", average_times)
# #     # Plotting results
# #     fig, ax = plt.subplots(1, 2, figsize=(12, 6))

# #     for idx, p_eve in enumerate(p_eve_values):
# #         ax[0].bar([str(key_size) for key_size in key_sizes], [average_times[key_size][p_eve] for key_size in key_sizes], alpha=0.5, label=f'p_eve={p_eve}')
# #         ax[1].plot([str(key_size) for key_size in key_sizes], [average_times[key_size][p_eve] for key_size in key_sizes], marker='o', linestyle='-', label=f'p_eve={p_eve}')

# #     ax[0].set_xlabel('Key Size')
# #     ax[0].set_ylabel('Average Establishment Time (seconds)')
# #     ax[0].set_title('Average Establishment Time vs Key Size')
# #     ax[0].legend()
# #     ax[0].grid(True)

# #     ax[1].set_xlabel('Key Size')
# #     ax[1].set_ylabel('Average Establishment Time (seconds)')
# #     ax[1].set_title('Average Establishment Time vs Key Size')
# #     ax[1].legend()
# #     ax[1].grid(True)

# #     plt.tight_layout()
# #     plt.show()


# if __name__ == '__main__':
#     main()


from qunetsim.components.host import Host
from qunetsim.components.network import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger
import random
import numpy as np
import matplotlib.pyplot as plt
import time

Logger.DISABLED = True
WAIT_TIME = 500
INTERCEPTION = True


# Basis Declaration
BASIS = ['Z', 'X']  # |0>|1> = Z-Basis; |+>|-> = X-Basis
##########################################################################


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



def preparation(key_length):
    alice_basis = ""
    bob_basis = ""
    alice_bits = ""
    for kl in range(key_length):
        alice_basis += random.choice(BASIS)
        bob_basis += random.choice(BASIS)
        alice_bits += str(random.getrandbits(1))
    alice_encoded = encoded_bases(alice_bits, alice_basis)
    return alice_basis, bob_basis, alice_bits, alice_encoded

def select_eavesdropping_indices(p_eve, key_length):
    return random.sample(range(key_length), int(p_eve * key_length))


def alice_key_string(alice_bits, alice_basis, bob_basis, eavesdrop_indices):
    alice_key = ""
    for i in range(len(alice_bits)):
        if i not in eavesdrop_indices and alice_basis[i] == bob_basis[i]:
            alice_key += str(alice_bits[i])
    return alice_key


def bob_key_string(bob_bits, bob_basis, alice_basis, eavesdrop_indices):
    bob_key = ""
    for i in range(len(bob_bits)):
        if i not in eavesdrop_indices and bob_basis[i] == alice_basis[i]:
            bob_key += str(bob_bits[i])
    return bob_key



def alice(host, receiver, alice_basis, alice_bits, alice_encoded, p_eve):
    eavesdrop_indices = select_eavesdropping_indices(p_eve, len(alice_bits))

    print("Sample indices used for error detection {}".format(eavesdrop_indices))
    # detection_percentage = (len(sample_indices)/KEY_LENGTH) * 100
    # print("Percentage of qubits used for eavesdropping (error) detection: {:.2f}%".format(detection_percentage))

    qubits_sent_count = 0

    # For Qubit and Basis
    for i, encode in enumerate(alice_encoded):
        _, ack = host.send_qubit(receiver, q_bit(host,encode), await_ack=True)
        if ack is not None:
            qubits_sent_count+=1
            # print("{}'s qubit {} successfully sent".format(host.host_id, i))
    ################################################################################
    
    print("Number of qubits sent by Alice: {}".format(qubits_sent_count))

    # Sending Basis to Bob
    ack_basis_alice = host.send_classical(receiver, (alice_basis,eavesdrop_indices), await_ack=True)
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
    alice_key = alice_key_string(alice_bits, alice_basis, bob_basis, eavesdrop_indices)
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
    
    return alice_key
    ################################################################################


def eve_sniffing_quantum(sender, receiver, qubit):
    qubit.measure(non_destructive=True)


def bob(host, receiver, bob_basis, p_eve):
    bob_measured_bits = ""
    qubits_received_count = 0
    # For Qubit and Basis
    for i in range(0, len(bob_basis)):
        data = host.get_qubit(receiver, wait=WAIT_TIME)
        if data is not None:
            qubits_received_count += 1
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
        alice_basis, eavesdrop_indices = basis_from_alice[0].content
        print('Alice_basis', alice_basis)
        print("These are the sample indices", eavesdrop_indices)
        # print("Content from basis of alice" , basis_from_alice[0].content)
        # exit()
        print("{}'s basis string got successfully by {}".format(receiver, host.host_id))
    # Sending Basis to Alice
    # exit()
    # exit()
    ack_basis_bob = host.send_classical(receiver, bob_basis, await_ack=True)
    if ack_basis_bob is not None:
        print("{}'s basis string successfully sent".format(host.host_id))
    ################################################################################

    # For sample key indices
    bob_key = bob_key_string(bob_measured_bits, bob_basis, alice_basis, eavesdrop_indices)
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

    # error_count = sum(1 for i in sample_indices if alice_basis[i] != bob_basis[i] or alice_bits[i] != bob_measured_bits[i])
    # error_rate = error_count / len(sample_indices)
    # print("Error Rate: {:.2%}".format(error_rate))

    return bob_key,bob_measured_bits


def main():

    key_sizes = [128,256,512,1024]
    p_eve_values = [0.5]
    key_lengths = [31,67,124,244]
    # error_rates = [0.05]

     
    results = {key_length: {p_eve: [] for p_eve in p_eve_values} for key_length in key_lengths}
    num_runs = 0
    for _ in range(1):
        num_runs+=1
        for i in range(len(key_sizes)):
            for p_eve in p_eve_values:
                
                random.seed(42)
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
                
                alice_basis, bob_basis, alice_bits, alice_encoded = preparation(key_sizes[i])
                print("Alice bases: {}".format(alice_basis))
                print("Bob bases: {}".format(bob_basis))
                print("Alice bits: {}".format(alice_bits))
                print("Alice encoded: {}".format(alice_encoded))

                if INTERCEPTION:
                    host_eve.q_relay_sniffing = True
                    host_eve.q_relay_sniffing_fn = eve_sniffing_quantum

                start_time = time.time()

                t1 = host_alice.run_protocol(alice, (host_bob.host_id, alice_basis, alice_bits, alice_encoded, p_eve,))
                t2 = host_bob.run_protocol(bob, (host_alice.host_id, bob_basis, p_eve ))
                t1.join()
                t2.join()

                end_time = time.time()

                elapsed_time = end_time - start_time
                results[key_lengths[i]][p_eve].append(elapsed_time)


                network.stop(True)
                time.sleep(2)
        print("runs completed : ", num_runs)
    # Calculate average times
    average_times = {key_length: {p_eve: np.mean(results[key_length][p_eve]) for p_eve in p_eve_values} for key_length in key_lengths}
    print("Average Times", average_times)
    # Plotting results
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    for idx, p_eve in enumerate(p_eve_values):
        ax[0].bar([str(key_length) for key_length in key_lengths], [average_times[key_length][p_eve] for key_length in key_lengths], alpha=0.5, label=f'p_eve={p_eve}')
        ax[1].plot([str(key_length) for key_length in key_lengths], [average_times[key_length][p_eve] for key_length in key_lengths], marker='o', linestyle='-', label=f'p_eve={p_eve}')

    ax[0].set_xlabel('Secure Key Size')
    ax[0].set_ylabel('Average Establishment Time (seconds)')
    ax[0].set_title('Average Establishment Time vs Key Size')
    ax[0].legend()
    ax[0].grid(True)

    ax[1].set_xlabel('Secure Key Size')
    ax[1].set_ylabel('Average Establishment Time (seconds)')
    ax[1].set_title('Average Establishment Time vs Key Size')
    ax[1].legend()
    ax[1].grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()


# {62: {0.1: 61.32380676269531}, 121: {0.1: 119.14356589317322}, 233: {0.1: 234.91516757011414}, 450: {0.1: 465.81179118156433}}
# {31: {0.5: 61.0752170085907}, 67: {0.5: 118.76208925247192}, 124: {0.5: 235.38785529136658}, 244: {0.5: 465.4741563796997}}