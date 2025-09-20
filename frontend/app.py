import streamlit as st
from backend.qkd import QKDSimulator
from qiskit import QuantumCircuit
import matplotlib.pyplot as plt
from PIL import Image
import io
import pandas as pd
import random

def draw_single_qubit_circuit(bit, alice_basis, bob_basis, eve_present=False):
    """Draw single-qubit BB84 circuit"""
    qc = QuantumCircuit(1, 1)
    
    # Alice's operations
    if bit == 1:
        qc.x(0)
    if alice_basis == 'x':
        qc.h(0)
    
    # Eve's interception
    if eve_present:
        qc.barrier()
        # Eve measures in random basis
        eve_basis = random.choice(['+', 'x'])
        if eve_basis == 'x':
            qc.h(0)
        qc.measure(0, 0)
        qc.reset(0)
        # Re-prepare based on measurement
        if eve_basis == 'x':
            qc.h(0)
        qc.barrier()
    
    # Bob's measurement
    if bob_basis == 'x':
        qc.h(0)
    qc.measure(0, 0)
    
    # Draw circuit
    fig = qc.draw(output='mpl', style='clifford', initial_state=True)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf)
    plt.close(fig)
    return img

def format_quantum_state(state):
    """Convert state to human-readable notation"""
    if isinstance(state, str):
        return state
    if '0' in state and abs(state['0'] - 1) < 0.01:
        return "|0⟩"
    elif '1' in state and abs(state['1'] - 1) < 0.01:
        return "|1⟩"
    elif all(abs(abs(v)-0.707) < 0.01 for v in state.values()):
        if abs(state['1'] - 0.707) < 0.01:
            return "|+⟩"
        else:
            return "|-⟩"
    return "Unknown"

def main():
    st.title("Quantum Key Distribution (QKD) Simulator")
    st.markdown("""
    ### BB84 Protocol Demonstration
    - **Z-basis**: |0⟩ and |1⟩ states
    - **X-basis**: |+⟩ and |-⟩ states
    """)
    
    # Sidebar controls
    st.sidebar.header("Simulation Parameters")
    key_length = st.sidebar.slider("Key Length", 5, 100, 28)
    eve_presence = st.sidebar.checkbox("Include Eve (eavesdropper)")
    
    if st.sidebar.button("Run Simulation"):
        # Initialize and run simulation
        qkd = QKDSimulator(key_length)
        results = qkd.run_simulation(eve_presence)
        
        # Display results
        st.header("Simulation Results")
        
        # 1. Single-qubit circuit diagram
        st.subheader("Protocol Steps (Single Qubit Example)")
        circuit_img = draw_single_qubit_circuit(
            results['alice_bits'][0],
            results['alice_bases'][0],
            results['bob_bases'][0],
            eve_presence
        )
        st.image(circuit_img, use_container_width=True)
        
        # 2. All Alice's original bits and bases
        st.subheader("Alice's Original Data")
        alice_data = pd.DataFrame({
            "Qubit Index": range(key_length),
            "Alice's Bits": results['alice_bits'],
            "Alice's Bases": ["Z" if b == "+" else "X" for b in results['alice_bases']]
        })
        st.dataframe(alice_data, hide_index=True)
        
        # 4. Basis information
        st.subheader("Basis Choices")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Alice's Bases**")
            st.write(["Z" if b == "+" else "X" for b in results['alice_bases']])
        with col2:
            st.markdown("**Bob's Bases**")
            st.write(["Z" if b == "+" else "X" for b in results['bob_bases']])
        with col3:
            if eve_presence:
                st.markdown("**Eve's Bases**")
                st.write(["Z" if b == "+" else "X" for b in results['eve_bases']])
        
        # 5. Sifted key table - only matching bases
        st.subheader("Sifted Key Results (Matching Bases Only)")
        matching_indices = [i for i in range(key_length) 
                          if results['alice_bases'][i] == results['bob_bases'][i]]
        
        sifted_table = pd.DataFrame({
            "Qubit Index": matching_indices,
            "Alice's Bit": [results['alice_bits'][i] for i in matching_indices],
            "Bob's Result": [results['bob_results'][i] for i in matching_indices],
            "Match?": ["✅" if results['alice_bits'][i] == results['bob_results'][i] 
                     else "❌" for i in matching_indices]
        })
        
        st.dataframe(sifted_table, hide_index=True)
        
        # 6. Final key
        st.subheader("Final Shared Key")
        final_key = ''.join([str(results['alice_bits'][i]) 
                          for i in matching_indices 
                          if results['alice_bits'][i] == results['bob_results'][i]])
        
        if final_key:
            st.success(f"**Secure Key:** `{final_key}`")
            st.write(f"**Key Length:** {len(final_key)} bits")
            
            if eve_presence:
                error_count = sum(1 for i in matching_indices 
                                if results['alice_bits'][i] != results['bob_results'][i])
                error_rate = error_count / len(matching_indices) if matching_indices else 0
                expected_error_rate = 0.25  # Theoretical value for Eve's interference
                st.warning(f"Eve introduced {error_count} errors ({error_rate:.1%} error rate)")
                st.warning(f"Expected error rate from Eve: {expected_error_rate:.1%}")
        else:
            st.error("Key exchange failed - no matching bases or too many errors!")

if __name__ == "__main__":
    main()