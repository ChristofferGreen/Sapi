# 02-quantum-supremacy-using-a-programmable-superconducting-processor

Article

Quantum supremacy using a programmable
superconducting processor

https://doi.org/10.1038/s41586-019-1666-5                       Frank Arute1, Kunal Arya1, Ryan Babbush1, Dave Bacon1, Joseph C. Bardin1,2, Rami Barends1,
                                                                Rupak Biswas3, Sergio Boixo1, Fernando G. S. L. Brandao1,4, David A. Buell1, Brian Burkett1,
Received: 22 July 2019
                                                                Yu Chen1, Zijun Chen1, Ben Chiaro5, Roberto Collins1, William Courtney1, Andrew Dunsworth1,
Accepted: 20 September 2019                                     Edward Farhi1, Brooks Foxen1,5, Austin Fowler1, Craig Gidney1, Marissa Giustina1, Rob Graff1,
                                                                Keith Guerin1, Steve Habegger1, Matthew P. Harrigan1, Michael J. Hartmann1,6, Alan Ho1,
Published online: 23 October 2019
                                                                Markus Hoffmann1, Trent Huang1, Travis S. Humble7, Sergei V. Isakov1, Evan Jeffrey1,
                                                                Zhang Jiang1, Dvir Kafri1, Kostyantyn Kechedzhi1, Julian Kelly1, Paul V. Klimov1, Sergey Knysh1,
                                                                Alexander Korotkov1,8, Fedor Kostritsa1, David Landhuis1, Mike Lindmark1, Erik Lucero1,
                                                                Dmitry Lyakh9, Salvatore Mandrà3,10, Jarrod R. McClean1, Matthew McEwen5,
                                                                Anthony Megrant1, Xiao Mi1, Kristel Michielsen11,12, Masoud Mohseni1, Josh Mutus1,
                                                                Ofer Naaman1, Matthew Neeley1, Charles Neill1, Murphy Yuezhen Niu1, Eric Ostby1,
                                                                Andre Petukhov1, John C. Platt1, Chris Quintana1, Eleanor G. Rieffel3, Pedram Roushan1,
                                                                Nicholas C. Rubin1, Daniel Sank1, Kevin J. Satzinger1, Vadim Smelyanskiy1, Kevin J. Sung1,13,
                                                                Matthew D. Trevithick1, Amit Vainsencher1, Benjamin Villalonga1,14, Theodore White1,
                                                                Z. Jamie Yao1, Ping Yeh1, Adam Zalcman1, Hartmut Neven1 & John M. Martinis1,5*



                                                                The promise of quantum computers is that certain computational tasks might be
                                                                executed exponentially faster on a quantum processor than on a classical processor1. A
                                                                fundamental challenge is to build a high-fidelity processor capable of running quantum
                                                                algorithms in an exponentially large computational space. Here we report the use of a
                                                                processor with programmable superconducting qubits2–7 to create quantum states on
                                                                53 qubits, corresponding to a computational state-space of dimension 253 (about 1016).
                                                                Measurements from repeated experiments sample the resulting probability
                                                                distribution, which we verify using classical simulations. Our Sycamore processor takes
                                                                about 200 seconds to sample one instance of a quantum circuit a million times—our
                                                                benchmarks currently indicate that the equivalent task for a state-of-the-art classical
                                                                supercomputer would take approximately 10,000 years. This dramatic increase in
                                                                speed compared to all known classical algorithms is an experimental realization of
                                                                quantum supremacy8–14 for this specific computational task, heralding a much-
                                                                anticipated computing paradigm.


In the early 1980s, Richard Feynman proposed that a quantum computer                                In reaching this milestone, we show that quantum speedup is achiev-
would be an effective tool with which to solve problems in physics                               able in a real-world system and is not precluded by any hidden physical
and chemistry, given that it is exponentially costly to simulate large                           laws. Quantum supremacy also heralds the era of noisy intermediate-
quantum systems with classical computers1. Realizing Feynman’s vision                            scale quantum (NISQ) technologies15. The benchmark task we demon-
poses substantial experimental and theoretical challenges. First, can                            strate has an immediate application in generating certifiable random
a quantum system be engineered to perform a computation in a large                               numbers (S. Aaronson, manuscript in preparation); other initial uses
enough computational (Hilbert) space and with a low enough error                                 for this new computational capability may include optimization16,17,
rate to provide a quantum speedup? Second, can we formulate a prob-                              machine learning18–21, materials science and chemistry22–24. However,
lem that is hard for a classical computer but easy for a quantum com-                            realizing the full promise of quantum computing (using Shor’s algorithm
puter? By computing such a benchmark task on our superconducting                                 for factoring, for example) still requires technical leaps to engineer
qubit processor, we tackle both questions. Our experiment achieves                               fault-tolerant logical qubits25–29.
quantum supremacy, a milestone on the path to full-scale quantum                                    To achieve quantum supremacy, we made a number of techni-
computing8–14.                                                                                   cal advances which also pave the way towards error correction. We

Google AI Quantum, Mountain View, CA, USA. 2Department of Electrical and Computer Engineering, University of Massachusetts Amherst, Amherst, MA, USA. 3Quantum Artificial Intelligence
1


Laboratory (QuAIL), NASA Ames Research Center, Moffett Field, CA, USA. 4Institute for Quantum Information and Matter, Caltech, Pasadena, CA, USA. 5Department of Physics, University of
California, Santa Barbara, CA, USA. 6Friedrich-Alexander University Erlangen-Nürnberg (FAU), Department of Physics, Erlangen, Germany. 7Quantum Computing Institute, Oak Ridge National
Laboratory, Oak Ridge, TN, USA. 8Department of Electrical and Computer Engineering, University of California, Riverside, CA, USA. 9Scientific Computing, Oak Ridge Leadership Computing,
Oak Ridge National Laboratory, Oak Ridge, TN, USA. 10Stinger Ghaffarian Technologies Inc., Greenbelt, MD, USA. 11Institute for Advanced Simulation, Jülich Supercomputing Centre,
Forschungszentrum Jülich, Jülich, Germany. 12RWTH Aachen University, Aachen, Germany. 13Department of Electrical Engineering and Computer Science, University of Michigan, Ann Arbor,
MI, USA. 14Department of Physics, University of Illinois at Urbana-Champaign, Urbana, IL, USA. *e-mail: jmartinis@google.com



                                                                                                                               Nature | Vol 574 | 24 OCTOBER 2019 | 505

Article
developed fast, high-fidelity gates that can be executed simultaneously        a
across a two-dimensional qubit array. We calibrated and benchmarked
the processor at both the component and system level using a powerful
new tool: cross-entropy benchmarking11. Finally, we used component-
level fidelities to accurately predict the performance of the whole sys-
tem, further showing that quantum information behaves as expected
when scaling to large systems.


A suitable computational task
To demonstrate quantum supremacy, we compare our quantum proces-
sor against state-of-the-art classical computers in the task of sampling
the output of a pseudo-random quantum circuit11,13,14. Random circuits
are a suitable choice for benchmarking because they do not possess
structure and therefore allow for limited guarantees of computational
hardness10–12. We design the circuits to entangle a set of quantum bits
(qubits) by repeated application of single-qubit and two-qubit logi-
cal operations. Sampling the quantum circuit’s output produces a set                                      Qubit               Adjustable coupler
of bitstrings, for example {0000101, 1011100, …}. Owing to quantum
interference, the probability distribution of the bitstrings resembles         b
a speckled intensity pattern produced by light interference in laser
scatter, such that some bitstrings are much more likely to occur than
others. Classically computing this probability distribution becomes
exponentially more difficult as the number of qubits (width) and number
of gate cycles (depth) grow.
   We verify that the quantum processor is working properly using a
method called cross-entropy benchmarking11,12,14, which compares how
often each bitstring is observed experimentally with its corresponding
ideal probability computed via simulation on a classical computer. For
a given circuit, we collect the measured bitstrings {xi} and compute the
linear cross-entropy benchmarking fidelity11,13,14 (see also Supplementary
Information), which is the mean of the simulated probabilities of the
bitstrings we measured:                                                                                                                     10 mm
                                  n
                         FXEB = 2 ⟨P(xi)⟩i − 1                          (1)
                                                                              Fig. 1 | The Sycamore processor. a, Layout of processor, showing a rectangular
                                                                              array of 54 qubits (grey), each connected to its four nearest neighbours with
where n is the number of qubits, P(xi) is the probability of bitstring xi     couplers (blue). The inoperable qubit is outlined. b, Photograph of the
computed for the ideal quantum circuit, and the average is over the           Sycamore chip.
observed bitstrings. Intuitively, FXEB is correlated with how often we
sample high-probability bitstrings. When there are no errors in the
quantum circuit, the distribution of probabilities is exponential (see        connectivity was chosen to be forward-compatible with error correc-
Supplementary Information), and sampling from this distribution will          tion using the surface code26. A key systems engineering advance of this
produce FXEB = 1 . On the other hand, sampling from the uniform               device is achieving high-fidelity single- and two-qubit operations, not
distribution will give ⟨P(xi)⟩i = 1/2n and produce FXEB = 0. Values of FXEB   just in isolation but also while performing a realistic computation with
between 0 and 1 correspond to the probability that no error has occurred      simultaneous gate operations on many qubits. We discuss the highlights
while running the circuit. The probabilities P(xi) must be obtained from      below; see also the Supplementary Information.
classically simulating the quantum circuit, and thus computing FXEB is           In a superconducting circuit, conduction electrons condense into a
intractable in the regime of quantum supremacy. However, with certain         macroscopic quantum state, such that currents and voltages behave
circuit simplifications, we can obtain quantitative fidelity estimates of     quantum mechanically2,30. Our processor uses transmon qubits6, which
a fully operating processor running wide and deep quantum circuits.           can be thought of as nonlinear superconducting resonators at 5–7 GHz.
   Our goal is to achieve a high enough FXEB for a circuit with sufficient    The qubit is encoded as the two lowest quantum eigenstates of the
width and depth such that the classical computing cost is prohibitively       resonant circuit. Each transmon has two controls: a microwave drive
large. This is a difficult task because our logic gates are imperfect and     to excite the qubit, and a magnetic flux control to tune the frequency.
the quantum states we intend to create are sensitive to errors. A single      Each qubit is connected to a linear resonator used to read out the qubit
bit or phase flip over the course of the algorithm will completely shuffle    state5. As shown in Fig. 1, each qubit is also connected to its neighbouring
the speckle pattern and result in close to zero fidelity11 (see also Sup-     qubits using a new adjustable coupler31,32. Our coupler design allows us
plementary Information). Therefore, in order to claim quantum suprem-         to quickly tune the qubit–qubit coupling from completely off to 40 MHz.
acy we need a quantum processor that executes the program with                One qubit did not function properly, so the device uses 53 qubits and
sufficiently low error rates.                                                 86 couplers.
                                                                                 The processor is fabricated using aluminium for metallization and
                                                                              Josephson junctions, and indium for bump-bonds between two silicon
Building a high-fidelity processor                                            wafers. The chip is wire-bonded to a superconducting circuit board
We designed a quantum processor named ‘Sycamore’ which consists               and cooled to below 20 mK in a dilution refrigerator to reduce ambient
of a two-dimensional array of 54 transmon qubits, where each qubit is         thermal energy to well below the qubit energy. The processor is con-
tunably coupled to four nearest neighbours, in a rectangular lattice. The     nected through filters and attenuators to room-temperature electronics,


506 | Nature | Vol 574 | 24 OCTOBER 2019

which synthesize the control signals. The state of all qubits can be read          a 1.00
simultaneously by using a frequency-multiplexing technique33,34. We use
two stages of cryogenic amplifiers to boost the signal, which is digitized
(8 bits at 1 GHz) and demultiplexed digitally at room temperature. In
total, we orchestrate 277 digital-to-analog converters (14 bits at 1 GHz)                                    0.75




                                                                                Integrated histogram, ECDF
for complete control of the quantum processor.
   We execute single-qubit gates by driving 25-ns microwave pulses reso-
                                                                                                                         e1         e2               e2c             er
nant with the qubit frequency while the qubit–qubit coupling is turned
                                                                                                             0.50
off. The pulses are shaped to minimize transitions to higher transmon
states35. Gate performance varies strongly with frequency owing to two-
level-system defects36,37, stray microwave modes, coupling to control
lines and the readout resonator, residual stray coupling between qubits,                                     0.25
flux noise and pulse distortions. We therefore optimize the single-qubit
operation frequencies to mitigate these error mechanisms.
                                                                                                                                                                    Isolated
   We benchmark single-qubit gate performance by using the cross-                                                                                                   Simultaneous
entropy benchmarking protocol described above, reduced to the single-                                        0.00
                                                                                                                      10–3                         10–2                      10–1
qubit level (n = 1), to measure the probability of an error occurring                                                             Pauli and measurement errors
during a single-qubit gate. On each qubit, we apply a variable number
m of randomly selected gates and measure FXEB averaged over many                                                        Average error          Isolated      Simultaneous
sequences; as m increases, errors accumulate and average FXEB decays.                                                 Single-qubit (e1)         0.15%            0.16%
We model this decay by [1 − e1/(1 − 1/D2)]m where e1 is the Pauli error prob-                                          Two-qubit (e2)           0.36%            0.62%
ability. The state (Hilbert) space dimension term, D = 2n, which equals                                             Two-qubit, cycle (e2c)      0.65%            0.93%
2 for this case, corrects for the depolarizing model where states with                                                  Readout (er)             3.1%            3.8%
errors partially overlap with the ideal state. This procedure is similar to       b
the more typical technique of randomized benchmarking27,38,39, but                                  Pauli error
supports non-Clifford-gate sets40 and can separate out decoherence                                    e1, e2
error from coherent control error. We then repeat the experiment with
all qubits executing single-qubit gates simultaneously (Fig. 2), which
                                                                                       10–2
shows only a small increase in the error probabilities, demonstrating
that our device has low microwave crosstalk.
   We perform two-qubit iSWAP-like entangling gates by bringing neigh-
bouring qubits on-resonance and turning on a 20-MHz coupling for 12 ns,
which allows the qubits to swap excitations. During this time, the qubits
also experience a controlled-phase (CZ) interaction, which originates
from the higher levels of the transmon. The two-qubit gate frequency
trajectories of each pair of qubits are optimized to mitigate the same error
mechanisms considered in optimizing single-qubit operation frequencies.
   To characterize and benchmark the two-qubit gates, we run two-qubit                 10–3
circuits with m cycles, where each cycle contains a randomly chosen
single-qubit gate on each of the two qubits followed by a fixed two-qubit
gate. We learn the parameters of the two-qubit unitary (such as the             Fig. 2 | System-wide Pauli and measurement errors. a, Integrated histogram
                                                                                (empirical cumulative distribution function, ECDF) of Pauli errors (black, green,
amount of iSWAP and CZ interaction) by using FXEB as a cost function.
                                                                                blue) and readout errors (orange), measured on qubits in isolation (dotted lines)
After this optimization, we extract the per-cycle error e2c from the decay
                                                                                and when operating all qubits simultaneously (solid). The median of each
of FXEB with m, and isolate the two-qubit error e2 by subtracting the two
                                                                                distribution occurs at 0.50 on the vertical axis. Average (mean) values are shown
single-qubit errors e1. We find an average e2 of 0.36%. Additionally, we
                                                                                below. b, Heat map showing single- and two-qubit Pauli errors e1 (crosses) and e2
repeat the same procedure while simultaneously running two-qubit                (bars) positioned in the layout of the processor. Values are shown for all qubits
circuits for the entire array. After updating the unitary parameters to         operating simultaneously.
account for effects such as dispersive shifts and crosstalk, we find an
average e2 of 0.62%.
   For the full experiment, we generate quantum circuits using the two-            Having found the error rates of the individual gates and readout, we
qubit unitaries measured for each pair during simultaneous operation,           can model the fidelity of a quantum circuit as the product of the prob-
rather than a standard gate for all pairs. The typical two-qubit gate is a      abilities of error-free operation of all gates and measurements. Our
full iSWAP with 1/6th of a full CZ. Using individually calibrated gates in      largest random quantum circuits have 53 qubits, 1,113 single-qubit gates,
no way limits the universality of the demonstration. One can compose,           430 two-qubit gates, and a measurement on each qubit, for which we
for example, controlled-NOT (CNOT) gates from 1-qubit gates and two             predict a total fidelity of 0.2%. This fidelity should be resolvable with a
of the unique 2-qubit gates of any given pair. The implementation of            few million measurements, since the uncertainty on FXEB is 1/ Ns , where
high-fidelity ‘textbook gates’ natively, such as CZ or iSWAP , is work          Ns is the number of samples. Our model assumes that entangling larger
in progress.                                                                    and larger systems does not introduce additional error sources beyond
   Finally, we benchmark qubit readout using standard dispersive meas-          the errors we measure at the single- and two-qubit level. In the next
urement41. Measurement errors averaged over the 0 and 1 states are              section we will see how well this hypothesis holds up.
shown in Fig. 2a. We have also measured the error when operating all
qubits simultaneously, by randomly preparing each qubit in the 0 or 1
state and then measuring all qubits for the probability of the correct          Fidelity estimation in the supremacy regime
result. We find that simultaneous readout incurs only a modest increase         The gate sequence for our pseudo-random quantum circuit generation
in per-qubit measurement errors.                                                is shown in Fig. 3. One cycle of the algorithm consists of applying


                                                                                                                                    Nature | Vol 574 | 24 OCTOBER 2019 | 507

Article
a                                                                                                                                           b
                                                                                                                                                  Single-qubit gate:
                                        0                                                                                                                25 ns
                                            W

                                        0                                                                                                     Qubit
                      C                      X                                                                                              XY control

            A                           0                                                                                                           Two-qubit gate:
                                             X
                                                                                                                                                        12 ns
                          B             0
                                                                                                                                              Qubit 1
                                                                                                                                             Z control
                D                           W

                                        0                                                                                                    Coupler
                                             Y
                                Column
                          Row                    A         B         C         D        C        D         A        B                         Qubit 2
                                   Time                                                                                                      Z control
                                      Cycle 1          2         3         4        5        6         7        8            m

Fig. 3 | Control operations for the quantum supremacy circuits. a, Example         couplers are divided into four subsets (ABCD), each of which is executed
quantum circuit instance used in our experiment. Every cycle includes a layer      simultaneously across the entire array corresponding to shaded colours. Here
each of single- and two-qubit gates. The single-qubit gates are chosen randomly    we show an intractable sequence (repeat ABCDCDAB); we also use different
from { X , Y , W }, where W = (X + Y )/ 2 and gates do not repeat sequentially.    coupler subsets along with a simplifiable sequence (repeat EFGHEFGH, not
The sequence of two-qubit gates is chosen according to a tiling pattern,           shown) that can be simulated on a classical computer. b, Waveform of control
coupling each qubit sequentially to its four nearest-neighbour qubits. The         signals for single- and two-qubit gates.


single-qubit gates chosen randomly from { X , Y , W } on all qubits,               of running these circuits on the quantum processor is greater than at
followed by two-qubit gates on pairs of qubits. The sequences of gates             least 0.1%. We expect that the full data for Fig. 4b should have similar
which form the ‘supremacy circuits’ are designed to minimize the circuit           fidelities, but since the simulation times (red numbers) take too long to
depth required to create a highly entangled state, which is needed for             check, we have archived the data (see ‘Data availability’ section). The
computational complexity and classical hardness.                                   data is thus in the quantum supremacy regime.
   Although we cannot compute FXEB in the supremacy regime, we can
estimate it using three variations to reduce the complexity of the circuits.
In ‘patch circuits’, we remove a slice of two-qubit gates (a small fraction        The classical computational cost
of the total number of two-qubit gates), splitting the circuit into two            We simulate the quantum circuits used in the experiment on classical
spatially isolated, non-interacting patches of qubits. We then compute             computers for two purposes: (1) verifying our quantum processor and
the total fidelity as the product of the patch fidelities, each of which can       benchmarking methods by computing FXEB where possible using sim-
be easily calculated. In ‘elided circuits’, we remove only a fraction of the       plifiable circuits (Fig. 4a), and (2) estimating FXEB as well as the classical
initial two-qubit gates along the slice, allowing for entanglement                 cost of sampling our hardest circuits (Fig. 4b). Up to 43 qubits, we use
between patches, which more closely mimics the full experiment while               a Schrödinger algorithm, which simulates the evolution of the full quan-
still maintaining simulation feasibility. Finally, we can also run full            tum state; the Jülich supercomputer (with 100,000 cores, 250 terabytes)
‘verification circuits’, with the same gate counts as our supremacy cir-           runs the largest cases. Above this size, there is not enough random access
cuits, but with a different pattern for the sequence of two-qubit gates,           memory (RAM) to store the quantum state42. For larger qubit numbers,
which is much easier to simulate classically (see also Supplementary               we use a hybrid Schrödinger–Feynman algorithm43 running on Google
Information). Comparison between these three variations allows us to               data centres to compute the amplitudes of individual bitstrings. This
track the system fidelity as we approach the supremacy regime.                     algorithm breaks the circuit up into two patches of qubits and efficiently
   We first check that the patch and elided versions of the verification           simulates each patch using a Schrödinger method, before connecting
circuits produce the same fidelity as the full verification circuits up to         them using an approach reminiscent of the Feynman path-integral.
53 qubits, as shown in Fig. 4a. For each data point, we typically collect          Although it is more memory-efficient, the Schrödinger–Feynman algo-
Ns = 5 × 106 total samples over ten circuit instances, where instances             rithm becomes exponentially more computationally expensive with
differ only in the choices of single-qubit gates in each cycle. We also            increasing circuit depth owing to the exponential growth of paths with
show predicted FXEB values, computed by multiplying the no-error prob-             the number of gates connecting the patches.
abilities of single- and two-qubit gates and measurement (see also Sup-               To estimate the classical computational cost of the supremacy circuits
plementary Information). The predicted, patch and elided fidelities all            (grey numbers in Fig. 4b), we ran portions of the quantum circuit simu-
show good agreement with the fidelities of the corresponding full cir-             lation on both the Summit supercomputer as well as on Google clusters
cuits, despite the vast differences in computational complexity and                and extrapolated to the full cost. In this extrapolation, we account for
entanglement. This gives us confidence that elided circuits can be used            the computation cost of sampling by scaling the verification cost with
to accurately estimate the fidelity of more-complex circuits.                      FXEB, for example43,44, a 0.1% fidelity decreases the cost by about 1,000.
   The largest circuits for which the fidelity can still be directly verified      On the Summit supercomputer, which is currently the most powerful
have 53 qubits and a simplified gate arrangement. Performing random                in the world, we used a method inspired by Feynman path-integrals that
circuit sampling on these at 0.8% fidelity takes one million cores 130             is most efficient at low depth44–47. At m = 20 the tensors do not reason-
seconds, corresponding to a million-fold speedup of the quantum pro-               ably fit into node memory, so we can only measure runtimes up to m = 14,
cessor relative to a single core.                                                  for which we estimate that sampling three million bitstrings with 1%
   We proceed now to benchmark our computationally most difficult                  fidelity would require a year.
circuits, which are simply a rearrangement of the two-qubit gates. In                 On Google Cloud servers, we estimate that performing the same task
Fig. 4b, we show the measured FXEB for 53-qubit patch and elided ver-              for m = 20 with 0.1% fidelity using the Schrödinger–Feynman algorithm
sions of the full supremacy circuits with increasing depth. For the larg-          would cost 50 trillion core-hours and consume one petawatt hour of
est circuit with 53 qubits and 20 cycles, we collected Ns = 30 × 106 samples       energy. To put this in perspective, it took 600 seconds to sample the
over ten circuit instances, obtaining FXEB = (2.24 ±0.21) × 10−3 for the           circuit on the quantum processor three million times, where sampling
elided circuits. With 5σ confidence, we assert that the average fidelity           time is limited by control hardware communications; in fact, the net


508 | Nature | Vol 574 | 24 OCTOBER 2019

        a                                                                       Classically verifiable                                                  b                       Supremacy regime
                                       10 0




                                                                                                           E    F   G H    E    F   G H                                              A   B C D       C D     A     B
                     XEB




                                                                                                                           Sycamore sampling (Ns = 106): 200 s
Cross-entropy benchmarking fidelity,




                                       10–1
                                                                                                                                                              2h        Classical sampling at     Sycamore


                                                                                                                                                                           2 weeks
                                                                                                                          Classical verification            1 week
                                                                                                                                                                                          4 yr
                                                                                                                                                                             4 yr
                                                                                                                                            5h                                                      100 yr
                                                                                                                                                                                         600 yr
                                                                                                                                                                                                                 10,000 yr

                                       10–2    m = 14 cycles
                                                     Prediction from gate and measurement errors
                                                   Full circuit        Elided circuit      Patch circuit

                                                                                                                                                             n = 53 qubits
                                                                                                                                                                   Prediction
                                                                                                                                                                   Elided (±5V error bars)
                                                                                                                                                                   Patch
                                       10–3
                                          10        15         20         25        30        35           40        45             50             55         12             14       16          18                20
                                                                                 Number of qubits, n                                                                          Number of cycles, m

Fig. 4 | Demonstrating quantum supremacy. a, Verification of benchmarking                                             complexity, justifies the use of elided circuits to estimate fidelity in the
methods. F XEB values for patch, elided and full verification circuits are                                            supremacy regime. b, Estimating F XEB in the quantum supremacy regime. Here,
calculated from measured bitstrings and the corresponding probabilities                                               the two-qubit gates are applied in a non-simplifiable tiling and sequence for
predicted by classical simulation. Here, the two-qubit gates are applied in a                                         which it is much harder to simulate. For the largest elided data (n = 53, m = 20,
simplifiable tiling and sequence such that the full circuits can be simulated out                                     total Ns = 30 million), we find an average F XEB > 0.1% with 5σ confidence, where σ
to n = 53, m = 14 in a reasonable amount of time. Each data point is an average over                                  includes both systematic and statistical uncertainties. The corresponding full
ten distinct quantum circuit instances that differ in their single-qubit gates (for n                                 circuit data, not simulated but archived, is expected to show similarly
= 39, 42 and 43 only two instances were simulated). For each n, each instance is                                      statistically significant fidelity. For m = 20, obtaining a million samples on the
sampled with Ns of 0.5–2.5 million. The black line shows the predicted F XEB based                                    quantum processor takes 200 seconds, whereas an equal-fidelity classical
on single- and two-qubit gate and measurement errors. The close                                                       sampling would take 10,000 years on a million cores, and verifying the fidelity
correspondence between all four curves, despite their vast differences in                                             would take millions of years.


quantum processor time is only about 30 seconds. The bitstring samples                                                choosing circuits that randomize and decorrelate errors, by optimizing
from all circuits have been archived online (see ‘Data availability’ section)                                         control to minimize systematic errors and leakage, and by designing
to encourage development and testing of more advanced verification                                                    gates that operate much faster than correlated noise sources, such as
algorithms.                                                                                                           1/f flux noise37. Demonstrating a predictive uncorrelated error model
   One may wonder to what extent algorithmic innovation can enhance                                                   up to a Hilbert space of size 253 shows that we can build a system where
classical simulations. Our assumption, based on insights from complex-                                                quantum resources, such as entanglement, are not prohibitively fragile.
ity theory11–13, is that the cost of this algorithmic task is exponential in
circuit size. Indeed, simulation methods have improved steadily over the
past few years42–50. We expect that lower simulation costs than reported                                              The future
here will eventually be achieved, but we also expect that they will be                                                Quantum processors based on superconducting qubits can now perform
consistently outpaced by hardware improvements on larger quantum                                                      computations in a Hilbert space of dimension 253 ≈ 9 × 1015, beyond the
processors.                                                                                                           reach of the fastest classical supercomputers available today. To our
                                                                                                                      knowledge, this experiment marks the first computation that can be
                                                                                                                      performed only on a quantum processor. Quantum processors have
Verifying the digital error model                                                                                     thus reached the regime of quantum supremacy. We expect that their
A key assumption underlying the theory of quantum error correction                                                    computational power will continue to grow at a double-exponential
is that quantum state errors may be considered digitized and local-                                                   rate: the classical cost of simulating a quantum circuit increases expo-
ized38,51. Under such a digital model, all errors in the evolving quantum                                             nentially with computational volume, and hardware improvements will
state may be characterized by a set of localized Pauli errors (bit-flips or                                           probably follow a quantum-processor equivalent of Moore’s law52,53,
phase-flips) interspersed into the circuit. Since continuous amplitudes                                               doubling this computational volume every few years. To sustain the
are fundamental to quantum mechanics, it needs to be tested whether                                                   double-exponential growth rate and to eventually offer the computa-
errors in a quantum system could be treated as discrete and probabil-                                                 tional volume needed to run well known quantum algorithms, such as
istic. Indeed, our experimental observations support the validity of                                                  the Shor or Grover algorithms25,54, the engineering of quantum error
this model for our processor. Our system fidelity is well predicted by a                                              correction will need to become a focus of attention.
simple model in which the individually characterized fidelities of each                                                  The extended Church–Turing thesis formulated by Bernstein and
gate are multiplied together (Fig. 4).                                                                                Vazirani55 asserts that any ‘reasonable’ model of computation can be
   To be successfully described by a digitized error model, a system                                                  efficiently simulated by a Turing machine. Our experiment suggests
should be low in correlated errors. We achieve this in our experiment by                                              that a model of computation may now be available that violates this


                                                                                                                                                              Nature | Vol 574 | 24 OCTOBER 2019 | 509

Article
assertion. We have performed random quantum circuit sampling in                                   22.   Aspuru-Guzik, A., Dutoi, A. D., Love, P. J. & Head-Gordon, M. Simulated quantum
                                                                                                        computation of molecular energies. Science 309, 1704–1707 (2005).
polynomial time using a physically realizable quantum processor (with
                                                                                                  23.   Peruzzo, A. et al. A variational eigenvalue solver on a photonic quantum processor. Nat.
sufficiently low error rates), yet no efficient method is known to exist for                            Commun. 5, 4213 (2014).
classical computing machinery. As a result of these developments, quan-                           24.   Hempel, C. et al. Quantum chemistry calculations on a trapped-ion quantum simulator.
                                                                                                        Phys. Rev. X 8, 031022 (2018).
tum computing is transitioning from a research topic to a technology
                                                                                                  25.   Shor, P. W. Algorithms for quantum computation: discrete logarithms and factoring
that unlocks new computational capabilities. We are only one creative                                   proceedings. In Proc. 35th Ann. Symp. on Foundations of Computer Science https://doi.
algorithm away from valuable near-term applications.                                                    org/10.1109/SFCS.1994.365700 (IEEE, 1994).
                                                                                                  26.   Fowler, A. G., Mariantoni, M., Martinis, J. M. & Cleland, A. N. Surface codes: towards
                                                                                                        practical large-scale quantum computation. Phys. Rev. A 86, 032324 (2012).
                                                                                                  27.   Barends, R. et al. Superconducting quantum circuits at the surface code threshold for
Data availability                                                                                       fault tolerance. Nature 508, 500–503 (2014).
                                                                                                  28.   Córcoles, A. D. et al. Demonstration of a quantum error detection code using a square
The datasets generated and analysed for this study are available at our
                                                                                                        lattice of four superconducting qubits. Nat. Commun. 6, 6979 (2015).
public Dryad repository (https://doi.org/10.5061/dryad.k6t1rj8).                                  29.   Ofek, N. et al. Extending the lifetime of a quantum bit with error correction in
                                                                                                        superconducting circuits. Nature 536, 441 (2016).
                                                                                                  30.   Vool, U. & Devoret, M. Introduction to quantum electromagnetic circuits. Int. J. Circuit
                                                                                                        Theory Appl. 45, 897–934 (2017).
Online content                                                                                    31.   Chen, Y. et al. Qubit architecture with high coherence and fast tunable coupling circuits.
Any methods, additional references, Nature Research reporting summa-                                    Phys. Rev. Lett. 113, 220502 (2014).
                                                                                                  32.   Yan, F. et al. A tunable coupling scheme for implementing high-fidelity two-qubit gates.
ries, source data, extended data, supplementary information, acknowl-                                   Phys. Rev. Appl. 10, 054062 (2018).
edgements, peer review information; details of author contributions                               33.   Schuster, D. I. et al. Resolving photon number states in a superconducting circuit. Nature
and competing interests; and statements of data and code availability                                   445, 515 (2007).
                                                                                                  34.   Jeffrey, E. et al. Fast accurate state measurement with superconducting qubits. Phys. Rev.
are available at https://doi.org/10.1038/s41586-019-1666-5.                                             Lett. 112, 190504 (2014).
                                                                                                  35.   Chen, Z. et al. Measuring and suppressing quantum state leakage in a superconducting
                                                                                                        qubit. Phys. Rev. Lett. 116, 020501 (2016).
1.  Feynman, R. P. Simulating physics with computers. Int. J. Theor. Phys. 21, 467–488 (1982).
                                                                                                  36.   Klimov, P. V. et al. Fluctuations of energy-relaxation times in superconducting qubits.
2.  Devoret, M. H., Martinis, J. M. & Clarke, J. Measurements of macroscopic quantum
                                                                                                        Phys. Rev. Lett. 121, 090502 (2018).
    tunneling out of the zero-voltage state of a current-biased Josephson junction. Phys. Rev.
                                                                                                  37.   Yan, F. et al. The flux qubit revisited to enhance coherence and reproducibility. Nat.
    Lett. 55, 1908 (1985).
                                                                                                        Commun. 7, 12964 (2016).
3.  Nakamura, Y., Chen, C. D. & Tsai, J. S. Spectroscopy of energy-level splitting between two
                                                                                                  38.   Knill, E. et al. Randomized benchmarking of quantum gates. Phys. Rev. A 77, 012307
    macroscopic quantum states of charge coherently superposed by Josephson coupling.
                                                                                                        (2008).
    Phys. Rev. Lett. 79, 2328 (1997).
                                                                                                  39.   Magesan, E., Gambetta, J. M. & Emerson, J. Scalable and robust randomized
4. Mooij, J. et al. Josephson persistent-current qubit. Science 285, 1036–1039 (1999).
                                                                                                        benchmarking of quantum processes. Phys. Rev. Lett. 106, 180504 (2011).
5.  Wallraff, A. et al. Strong coupling of a single photon to a superconducting qubit using
                                                                                                  40.   Cross, A. W., Magesan, E., Bishop, L. S., Smolin, J. A. & Gambetta, J. M. Scalable
    circuit quantum electrodynamics. Nature 431, 162–167 (2004).
                                                                                                        randomised benchmarking of non-Clifford gates. npj Quant. Inform. 2, 16012 (2016).
6.  Koch, J. et al. Charge-insensitive qubit design derived from the Cooper pair box. Phys.
                                                                                                  41.   Wallraff, A. et al. Approaching unit visibility for control of a superconducting qubit with
    Rev. A 76, 042319 (2007).
                                                                                                        dispersive readout. Phys. Rev. Lett. 95, 060501 (2005).
7.  You, J. Q. & Nori, F. Atomic physics and quantum optics using superconducting circuits.
                                                                                                  42.   De Raedt, H. et al. Massively parallel quantum computer simulator, eleven years later.
    Nature 474, 589–597 (2011).
                                                                                                        Comput. Phys. Commun. 237, 47–61 (2019).
8.  Preskill, J. Quantum computing and the entanglement frontier. Rapporteur Talk at the
                                                                                                  43.   Markov, I. L., Fatima, A., Isakov, S. V. & Boixo, S. Quantum supremacy is both closer and
    25th Solvay Conference on Physics, Brussels https://doi.org/10.1142/8674 (World
                                                                                                        farther than it appears. Preprint at https://arxiv.org/abs/1807.10749 (2018).
    Scientific, 2012).
                                                                                                  44.   Villalonga, B. et al. A flexible high-performance simulator for the verification and
9.  Aaronson, S. & Arkhipov, A. The computational complexity of linear optics. In Proc. 43rd
                                                                                                        benchmarking of quantum circuits implemented on real hardware. npj Quant. Inform. (in
    Ann. Symp. on Theory of Computing https://doi.org/10.1145/1993636.1993682 (ACM,
                                                                                                        the press); preprint at https://arxiv.org/abs/1811.09599 (2018).
    2011).
                                                                                                  45.   Boixo, S., Isakov, S. V., Smelyanskiy, V. N. & Neven, H. Simulation of low-depth quantum
10. Bremner, M. J., Montanaro, A. & Shepherd, D. J. Average-case complexity versus
                                                                                                        circuits as complex undirected graphical models. Preprint at https://arxiv.org/
    approximate simulation of commuting quantum computations. Phys. Rev. Lett. 117,
                                                                                                        abs/1712.05384 (2017).
    080501 (2016).
                                                                                                  46.   Chen, J., Zhang, F., Huang, C., Newman, M. & Shi, Y. Classical simulation of intermediate-
11. Boixo, S. et al. Characterizing quantum supremacy in near-term devices. Nat. Phys. 14,
                                                                                                        size quantum circuits. Preprint at https://arxiv.org/abs/1805.01450 (2018).
    595 (2018).
                                                                                                  47.   Villalonga, B. et al. Establishing the quantum supremacy frontier with a 281 pflop/s
12. Bouland, A., Fefferman, B., Nirkhe, C. & Vazirani, U. On the complexity and verification of
                                                                                                        simulation. Preprint at https://arxiv.org/abs/1905.00444 (2019).
    quantum random circuit sampling. Nat. Phys. 15, 159 (2019).
                                                                                                  48.   Pednault, E. et al. Breaking the 49-qubit barrier in the simulation of quantum circuits.
13. Aaronson, S. & Chen, L. Complexity-theoretic foundations of quantum supremacy
                                                                                                        Preprint at https://arxiv.org/abs/1710.05867 (2017).
    experiments. In 32nd Computational Complexity Conf. https://doi.org/10.4230/LIPIcs.
                                                                                                  49.   Chen, Z. Y. et al. 64-qubit quantum circuit simulation. Sci. Bull. 63, 964–971 (2018).
    CCC.2017.22 (Schloss Dagstuhl–Leibniz Zentrum für Informatik, 2017).
                                                                                                  50.   Chen, M.-C. et al. Quantum-teleportation-inspired algorithm for sampling large random
14. Neill, C. et al. A blueprint for demonstrating quantum supremacy with superconducting
                                                                                                        quantum circuits. Preprint at https://arxiv.org/abs/1901.05003 (2019).
    qubits. Science 360, 195–199 (2018).
                                                                                                  51.   Shor, P. W. Scheme for reducing decoherence in quantum computer memory. Phys. Rev.
15. Preskill, J. Quantum computing in the NISQ era and beyond. Quantum 2, 79 (2018).
                                                                                                        A 52, R2493–R2496 (1995).
16. Kechedzhi, K. et al. Efficient population transfer via non-ergodic extended states in
                                                                                                  52.   Devoret, M. H. & Schoelkopf, R. J. Superconducting circuits for quantum information: an
    quantum spin glass. In 13th Conf. on the Theory of Quantum Computation,
                                                                                                        outlook. Science 339, 1169–1174 (2013).
    Communication and Cryptography http://drops.dagstuhl.de/opus/volltexte/2018/9256/
                                                                                                  53.   Mohseni, M. et al. Commercialize quantum technologies in five years. Nature 543, 171
    pdf/LIPIcs-TQC-2018-9.pdf (Schloss Dagstuhl–Leibniz Zentrum für Informatik, 2018).
                                                                                                        (2017).
17. Somma, R. D., Boixo, S., Barnum, H. & Knill, E. Quantum simulations of classical annealing
                                                                                                  54.   Grover, L. K. Quantum mechanics helps in searching for a needle in a haystack. Phys. Rev.
    processes. Phys. Rev. Lett. 101, 130504 (2008).
                                                                                                        Lett. 79, 325 (1997).
18. Farhi, E. & Neven, H. Classification with quantum neural networks on near term
                                                                                                  55.   Bernstein, E. & Vazirani, U. Quantum complexity theory. In Proc. 25th Ann. Symp. on
    processors. Preprint at https://arxiv.org/abs/1802.06002 (2018).
                                                                                                        Theory of Computing https://doi.org/10.1145/167088.167097 (ACM, 1993).
19. McClean, J. R., Boixo, S., Smelyanskiy, V. N., Babbush, R. & Neven, H. Barren plateaus in
    quantum neural network training landscapes. Nat. Commun. 9, 4812 (2018).
20. Cong, I., Choi, S. & Lukin, M. D. Quantum convolutional neural networks. Nat. Phys.           Publisher’s note Springer Nature remains neutral with regard to jurisdictional claims in
    https://doi.org/10.1038/s41567-019-0648-8 (2019).                                             published maps and institutional affiliations.
21. Bravyi, S., Gosset, D. & König, R. Quantum advantage with shallow circuits. Science 362,
    308–311 (2018).                                                                               © The Author(s), under exclusive licence to Springer Nature Limited 2019




510 | Nature | Vol 574 | 24 OCTOBER 2019

Acknowledgements We are grateful to E. Schmidt, S. Brin, S. Pichai, J. Dean, J. Yagnik and      Author contributions The Google AI Quantum team conceived the experiment. The
J. Giannandrea for their executive sponsorship of the Google AI Quantum team, and for           applications and algorithms team provided the theoretical foundation and the specifics of the
their continued engagement and support. We thank P. Norvig, J. Yagnik, U. Hölzle and            algorithm. The hardware team carried out the experiment and collected the data. The data
S. Pichai for advice on the manuscript. We acknowledge K. Kissel, J. Raso, D. L. Yonge-Mallo,   analysis was done jointly with outside collaborators. All authors wrote and revised the
O. Martin and N. Sridhar for their help with simulations. We thank G. Bortoli and               manuscript and the Supplementary Information.
L. Laws for keeping our team organized. This research used resources from the Oak Ridge
Leadership Computing Facility, which is a DOE Office of Science User Facility                   Competing interests The authors declare no competing interests.
(supported by contract DE-AC05-00OR22725). A portion of this work was performed in
the UCSB Nanofabrication Facility, an open access laboratory. R.B., S.M., and E.G.R.            Additional information
appreciate support from the NASA Ames Research Center and from the Air Force                    Supplementary information is available for this paper at https://doi.org/10.1038/s41586-019-
Research (AFRL) Information Directorate (grant F4HBKC4162G001). T.S.H. is supported             1666-5.
by the DOE Early Career Research Program. The views and conclusions contained herein            Correspondence and requests for materials should be addressed to J.M.M.
are those of the authors and should not be interpreted as necessarily representing the          Peer review information Nature thanks Scott Aaronson, Keisuke Fujii and William Oliver for
official policies or endorsements, either expressed or implied, of AFRL or the US               their contribution to the peer review of this work.
government.                                                                                     Reprints and permissions information is available at http://www.nature.com/reprints.
