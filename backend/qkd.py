from qiskit import QuantumCircuit, Aer, execute
from qiskit.quantum_info import Statevector
import random

class QKDSimulator:
    def __init__(self, key_length=10):
        self.key_length = key_length
        self.backend = Aer.get_backend('statevector_simulator')
        
    def _prepare_qubit(self, bit, basis):
        """Create a qubit in |0⟩, |1⟩, |+⟩ or |-⟩ state"""
        qc = QuantumCircuit(1)
        if bit == 1:
            qc.x(0)
        if basis == 'x':  # Hadamard basis
            qc.h(0)
        return qc
    
    def _measure_qubit(self, qc, basis):
        """Measure qubit in specified basis"""
        if basis == 'x':
            qc.h(0)
        qc.measure_all()
        return qc
    
    def run_simulation(self, eve_presence=False):
        # 1. Alice's preparations
        alice_bits = [random.randint(0, 1) for _ in range(self.key_length)]
        alice_bases = [random.choice(['+', 'x']) for _ in range(self.key_length)]
        
        # 2. Quantum channel transmission
        bob_bases = [random.choice(['+', 'x']) for _ in range(self.key_length)]
        eve_bases = None
        
        if eve_presence:
            eve_bases = [random.choice(['+', 'x']) for _ in range(self.key_length)]
        
        # 3. Simulate quantum transmission with measurements
        bob_results = []
        bell_pairs = []
        
        for i in range(self.key_length):
            # Alice prepares qubit
            qc = self._prepare_qubit(alice_bits[i], alice_bases[i])
            bell_pairs.append(Statevector(qc).to_dict())
            
            # Eve's interception (if present)
            if eve_presence:
                temp_qc = qc.copy()
                temp_qc = self._measure_qubit(temp_qc, eve_bases[i])
                result = execute(temp_qc, self.backend, shots=1).result()
                eve_bit = int(next(iter(result.get_counts())))
                
                # Eve re-prepares based on her measurement
                qc = self._prepare_qubit(eve_bit, eve_bases[i])
            
            # Bob measures
            qc = self._measure_qubit(qc, bob_bases[i])
            result = execute(qc, self.backend, shots=1).result()
            bob_results.append(int(next(iter(result.get_counts()))))
        
        # 4. Sift keys
        sifted_key = []
        for i in range(self.key_length):
            if alice_bases[i] == bob_bases[i]:
                sifted_key.append((alice_bits[i], bob_results[i]))
        
        # 5. Generate final key
        final_key = ''.join([str(a) for a, b in sifted_key if a == b])
        
        return {
            'alice_bits': alice_bits,
            'alice_bases': alice_bases,
            'bell_pairs': bell_pairs,  # Now shows actual quantum states
            'bob_bases': bob_bases,
            'eve_bases': eve_bases,
            'bob_results': bob_results,
            'sifted_key': sifted_key,
            'final_key': final_key,
            'eve_presence': eve_presence
        }