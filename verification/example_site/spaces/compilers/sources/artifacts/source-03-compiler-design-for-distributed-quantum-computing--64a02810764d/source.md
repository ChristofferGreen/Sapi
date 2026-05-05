# 03-compiler-design-for-distributed-quantum-computing

IEEE Transactions on
Quantum Internet                                                                                                                            uantum Engineering
Received August 3, 2020; revised October 19, 2020; accepted January 19, 2021; date of publication January 22, 2021;
date of current version March 18, 2021.
Digital Object Identifier 10.1109/TQE.2021.3053921




Compiler Design for Distributed
Quantum Computing
DAVIDE FERRARI1 (Graduate Student Member, IEEE),
ANGELA SARA CACCIAPUOTI2,3 (Senior Member, IEEE),
MICHELE AMORETTI1 (Senior Member, IEEE), AND
MARCELLO CALEFFI2,3 (Senior Member, IEEE)
1
  Department of Engineering and Architecture, University of Parma, 43124 Parma, Italy
2
  Future Communications Laboratory, Department of Electrical Engineering and Information Technology, University of Naples
Federico II, 80125 Naples, Italy
3
  Laboratorio Nazionale di Comunicazioni Multimediali, National Inter-University Consortium for Telecommunications, 80126
Naples, Italy
Corresponding author: Davide Ferrari (davide.ferrari1@unipr.it)
The work of Angela Sara Cacciapuoti and Marcello Caleffi was supported in part by the project “Towards the Quantum Internet: A
Multidisciplinary Effort,” University of Naples Federico II, Italy, and by the Italian MoD PNRM research program “QuaSaR:
Quantum” Safe netwoRk”.




ABSTRACT In distributed quantum computing architectures, with the network and communications func-
tionalities provided by the Quantum Internet, remote quantum processing units can communicate and
cooperate for executing computational tasks that single, noisy, intermediate-scale quantum devices cannot
handle by themselves. To this aim, distributed quantum computing requires a new generation of quantum
compilers, for mapping any quantum algorithm to any distributed quantum computing architecture. With this
perspective, in this article, we first discuss the main challenges arising with compiler design for distributed
quantum computing. Then, we analytically derive an upper bound of the overhead induced by quantum
compilation for distributed quantum computing. The derived bound accounts for the overhead induced by
the underlying computing architecture as well as the additional overhead induced by the suboptimal quantum
compiler—expressly designed in this article to achieve three key features, namely, general-purpose, efficient,
and effective. Finally, we validate the analytical results, and we confirm the validity of the compiler design
through an extensive performance analysis.
INDEX TERMS Distributed quantum computing, distributed quantum systems, quantum compiling, quan-
tum Internet, quantum networks.


I. INTRODUCTION                                                                                QPUs [13]—for executing computational tasks that each
Current quantum computers are commonly defined as                                              NISQ device cannot handle by itself.
noisy intermediate-scale quantum (NISQ) devices, being                                            As overviewed in recent literature such as [4] and [13],
characterized by a few dozens of quantum bits (qubits)                                         several challenges arise with the design of a distributed quan-
with nonuniform quality and highly constrained physical                                        tum computing architecture. In the following, we focus on
connectivity.                                                                                  the problem of designing a quantum algorithm compiler for
   Hence, the growing demand for large-scale quantum com-                                      distributed quantum compilation.
puters is motivating research on distributed quantum com-                                         Compiling a quantum algorithm means translating a
puting architectures [1]–[3], and experimental efforts have                                    hardware-agnostic description of the algorithm—i.e., the
demonstrated some of the building blocks for such a de-                                        quantum circuit1 —into a functionally equivalent one that
sign [4]. Indeed, with the network and communication func-                                     takes into account the physical constraints of the underlying
tionalities provided by the Quantum Internet [2], [3], [5]–                                    computing architecture—i.e., the compiled quantum circuit.
[12], remote quantum processing units (QPUs) can com-                                          When it comes to distributed computing architectures, there
municate and cooperate—through the distributed computing                                       are two main issues arising with the compiler design.
paradigm as a virtual quantum processor with a number
of qubits that scales linearly with the number of remote                                         1 See Section II for a proper introduction to quantum circuits, circuit
                                                                                               compilation, and circuit depth.

                     This work is licensed under a Creative Commons Attribution 4.0 License. For more information, see http://creativecommons.org/licenses/by/4.0/
VOLUME 2, 2021                                                                                                                                                       4100720

    IEEE Transactions on
    uantum Engineering                                            Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




   First, a fundamental question arises with distributed com-
putation: at what price? Indeed, distributed computation re-
quires the different processors being able to communicate
with each other for coordinating and data exchanging, and
these tasks introduce an overhead that strongly depend on
the particulars of the distributed computing architecture. For
instance, the induced overhead becomes more severe as the
connectivity between the QPUs shrinks or as the number of
qubits stored at the QPUs decreases. Hence, from a compil-
ing perspective, it is crucial to estimate the overhead effects
onto the compiled quantum circuit, effects that are generally
measured in terms of depth of the compiled circuit with re-       FIG. 1. Example of a 5-qubit quantum circuit from [18], with each
spect to the depth of the original one.                           horizontal line representing the time evolution of the state of a single
   Furthermore, compiling a quantum circuit is a very chal-       logical qubit.

lenging task even for a single-processor architecture, being
such a task an NP-complete problem [14]. Hence, optimal           analytical derivation of the overhead bound given in Sec-
circuit compiling for distributed quantum architectures can       tion IV. Then, Section V presents the performance analysis
be achieved only for very small circuit instances. Conversely,    for the proposed compiler design. In particular, we present
the compilation of medium to large circuits of practical value    the implementation of a compiler that is able to cope with the
induces an additional overhead—whose severity depends on          worst-case scenario for a distributed quantum computing ar-
the suboptimality of the quantum compiler—that further in-        chitecture; we validate the compiling overhead upper bound;
creases the depth of the compiled circuit.                        we illustrate experimental results regarding the compilation
   With this in mind, in this article, we analytically derive     of several quantum circuits, with our compiler compared to
an upper bound of the overhead induced by quantum circuit         a state-of-the-art solution. Finally, Section VI concludes this
compilation for distributed quantum computing:                    article.
  1) by considering the overhead induced by the worst-case
                                                                  II. BACKGROUND
     scenario for a distributed quantum computing architec-
                                                                  We refer the reader to [15] for an introduction to the concep-
     ture, namely, a scenario characterized by a) the lowest
                                                                  tual and notation differences separating quantum computing
     possible number of qubits at each QPU and b) the
                                                                  from conventional computing, and to [16] for an in-depth
     poorest connectivity among the QPUs;
                                                                  treatise of the subject.
  2) by considering the additional overhead induced by a
                                                                     In this article, we consider QPUs that support the quantum
     suboptimal quantum compiler.
                                                                  circuit model [17], which is the most popular and devel-
  Clearly, with reference to the last point, the additional       oped model for quantum computation. A quantum circuit is
overhead strongly depends on the particulars of the quantum       a model of a quantum algorithm, where quantum operators
compiler. To this aim, in this article, we design a quantum       are described as quantum gates. A quantum circuit is still a
compiler with three key features:                                 logical abstraction, not to be confused with its realization on
                                                                  an actual quantum hardware device. Hence, in the following,
  1) general-purpose, namely, requiring no particular as-         the abstract qubits subjected to quantum gates as specified
     sumptions on the quantum circuits to be compiled;            by the quantum circuit are called logical qubits to distinguish
  2) efficient, namely, exhibiting a polynomial-time compu-       them from the physical qubits embedded within a quantum
     tational complexity so that it can successfully compile      processor.
     medium-to-large circuits of practical value;                    Fig. 1 shows a simple quantum circuit, where each hor-
  3) effective, being the total circuit depth overhead induced    izontal line represents the time evolution of the state of a
     by the quantum circuit compilation always upper-             single logical qubit, with time flowing from left to right,
     bounded by a factor that grows linearly with the num-        dictating the order of execution of the different gates. More
     ber of logical qubits of the original quantum circuit.       specifically, gates affecting the same qubit must be executed
                                                                  sequentially, and this agrees with the intuition. Conversely,
   The rest of this article is organized as follows. In           gates acting on different qubits can be performed simulta-
Section II, we review some preliminaries about quantum            neously as long as the “ordering” arising from gates affect-
circuits and quantum compilers. Then, in Section III, we          ing multiple qubits is respected. This concept underlies the
detail the problem of circuit compilation for distributed quan-   notion of layer, i.e., the set of gates that can be performed
tum computing, discussing the challenges that arise with the      simultaneously on a disjoint set of qubits. The number of
compiler design and the relevant literature. These basics are     layers in a quantum circuit is denoted as circuit depth. As
crucial for understanding the compiler design as well as the      an example, the quantum circuit given in Fig. 1 is composed


4100720                                                                                                                       VOLUME 2, 2021

                                                                                                                   IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                                  uantum Engineering


                                                                             operations between adjacent physical qubits, as shown3 in
                                                                             Fig. 3.
                                                                                This process, known as quantum compilation, must be
                                                                             optimized so that the depth of the compiled circuit—i.e.,
                                                                             the equivalent quantum circuit satisfying all the constrains
FIG. 2. Coupling map of the IBM Melbourne quantum processor [22].            imposed by the quantum processor—is minimized [25], [26],
The 15 physical qubits are represented by circles. The arrows denote the
possibility to realize a two-qubit CNOT gate between the connected
                                                                             [28], [29].
qubits, with the arrow pointing toward the target qubit. As an example, a
CNOT between qubits Q1 (control) and Q0 (target) can be directly             III. COMPILERS FOR DISTRIBUTED
executed by the quantum processor, whereas a CNOT between qubits Q2
and Q0 cannot.                                                               QUANTUM COMPUTING
                                                                             As highlighted in Section I, the demand for large-scale quan-
                                                                             tum computers is motivating research on distributed quantum
of nine layers, and hence, its depth is equal to 9. The number
                                                                             computing architectures, where multiple small-scale quan-
of gates within the circuit is denoted as circuit size.
                                                                             tum processors interact and cooperate through the Quan-
                                                                             tum Internet for solving challenging computational tasks.
A. QUANTUM COMPILATION
                                                                             As a consequence, a new generation of quantum compilers
Given a quantum algorithm, there exist several equivalent
                                                                             is needed for mapping any quantum algorithm to any dis-
quantum circuits modeling the same computation with a dif-
                                                                             tributed quantum computing architecture.
ferent arrangement or different ordering of gates.
                                                                                Let us consider a toy model for distributed quantum com-
   Circuits with fewer gates—i.e., with lower size—may be
                                                                             puting, in which a generic quantum algorithm must be exe-
preferred to reduce the circuit complexity. However, the exe-
                                                                             cuted on two quantum processors interconnected by a quan-
cution time of the circuit—rather than its size—is generally
                                                                             tum link, as shown in Fig. 4.
considered the key factor to be optimized [19], [20]. The
rationale is to keep the execution time of the quantum circuit               A. CHALLENGES
within the coherence time of the underlying quantum hard-
                                                                             Several challenges arise with the design of a quantum com-
ware architecture [16], [21]. By oversimplifying, the execu-
                                                                             piler for mapping an arbitrary quantum circuit into a dis-
tion time increases with the number of layers. Therefore, it is
                                                                             tributed quantum computing architecture, as discussed in the
crucial to build—for a given quantum algorithm—a quantum
                                                                             following.
circuit characterized by the lowest possible depth. However,
two issues arise as a consequence of the quantum processor
                                                                             1) DATA QUBITS VERSUS COMMUNICATION QUBITS
characteristics.
   First, even if there exist an uncountable number of quan-                 Similarly to classical distributed computing, a key require-
tum logic gates, the set of gates that can be executed on a                  ment for distributed quantum computing is the possibility
certain quantum processor can be limited, as a consequence                   to perform remote operations, namely, operations between
of the constraints imposed by the underlying qubit technol-                  qubits stored at different processors. However, differently
ogy [4]. In this case, any gate outside this reduced set must                from the classical domain, quantum mechanics does not al-
be obtained with a proper combination of the allowed gates                   low an unknown qubit to be copied or even simply read or
through a process known as gate synthesis.                                   measured in any way, without causing an irreversible loss of
   Furthermore, regardless of the underlying qubit technol-                  the quantum information stored within the qubit [15], [16].
ogy, any quantum processor exhibits physical constraints—                       Thankfully, entanglement provides an invaluable tool for
arising as a consequence of the noise and the physical space                 implementing remote operations without violating quantum
limitations—on the possible interactions between the differ-                 mechanics [13]. Entanglement is a property of two (or more,
ent physical qubits. For example, CNOT gates cannot be ap-                   in case of multipartite entanglement) quantum particles that
plied to any physical qubit pair, but they are instead restricted            exist in a special type of superposition state, such that any
to certain pairs, as shown in Fig. 2, with the coupling map of               action on a particle affects instantaneously the other particle
an IBM quantum processor.                                                    as well. This sort of quantum correlation, with no counterpart
   From the above, it becomes clear that the execution of a                  in the classical world, holds even when the particles are far
quantum algorithm on a certain quantum processor requires                    away from each other. For an in-depth discussion about en-
that: 1) each logical qubit of the quantum circuit is mapped2                tanglement from an information engineering point of view,
onto a physical qubit of the quantum processor; and 2) each                  we refer the reader to [21].
CNOT operation between nonadjacent (within the coupling                         By exploiting the availability of a Bell state—that is a state
map) physical qubits is mapped into a sequence of CNOT                       of two maximally-enatngled qubits (EPR pairs, where EPR
                                                                             stands for Einstein, Podolsky, and Rosen)—shared between
   2 Indeed, NISQ technology may require a logical qubit to be mapped onto
                                                                             the two remote processors, it is possible to perform a remote
several physical qubits to implement proper fault-tolerant techniques [24]
Nevertheless, in the following, we assume a one-to-one mapping for the          3 With the state transfer strategy based on SWAPs usually preferred over
sake of clarity, without any loss of generality.                             the ancilla strategy [25]–[27].

VOLUME 2, 2021                                                                                                                                 4100720

     IEEE Transactions on
     uantum Engineering                                                          Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




FIG. 3. Example of equivalent quantum circuits generated during the quantum compilation for mapping an arbitrary CNOT into a sequence of CNOTs that
can be directly executed by a given quantum processor. (a) Reversing CNOT [23]. A CNOT between Q0 (control) and Q1 (target) can be executed with the
coupling map given in Fig. 2 by performing a CNOT between Q1 (control) and Q0 (target) sandwiched between two H gates. We note that the IBM
Melbourne processor (shown in Fig. 2) natively supports CNOTs in both directions between neighbor qubits. (b) CNOT between qubits Q0 (control) and
Q2 (target) can be executed through either: i) quantum state transfer, by first swapping qubits Q0 and Q1 so that Q0 and Q2 become adjacent qubits in
the coupling maps, then by performing a CNOT between Q0 and Q2 , and finally by swapping again qubits Q0 and Q1 so that they recover their initial
position, or ii) ancilla qubit, by performing four CNOT operations between neighbor qubits with the help of the intermediate qubit Q1 .




FIG. 4. Toy-model for distributed quantum computing, with two quantum processors interconnected through a quantum network. (a) shows the
network topology along with the processors coupling maps, whereas (b) provides the quantum circuit detailing the classical (2 bits) and the quantum
(the Bell state) resources needed to execute a remote operation. (a) Two IBM Yorktown quantum processors are interconnected with a quantum link
and a classical link. The classical link is used to transmit classical information, whereas the quantum link is needed to distribute Bell states—that is,
maximally entangled two-qubit states—between remote processors to execute remote operations. Indeed, at least one physical qubit at each processor
must be reserved for storing the Bell state, as discussed in (b). This kind of qubits—dark-blue-colored in the figure—are called communication qubits [3],
[30] to distinguish them from the remaining physical qubits—white-colored in the figure—devoted to computing and referred to as data qubits. (b)
Remote CNOT. To perform a CNOT between remote physical qubits stored at different processors—say data qubits Q4 and Q1 in (a)—a Bell state such as
+ must be distributed through the quantum link so that each pair member is stored within a communication qubit at each processor. Once the Bell
state is available, the remote CNOT is obtained with a local CNOT between the data and the communication qubit at each processor, followed by a
conditional gate on the data qubit depending on the measurement of the remote communication qubit. The double line denotes the transmission of 1
bit of classical information—i.e., the measurement output—between the remote processors.


CNOT through a sequence of local CNOTs and single-qubit                         the dedicated hardware—such as a matter-flying qubit in-
operations/measurements, as shown in Fig. 4(b).                                 terface [21]—required for entanglement distribution. Con-
   To distribute Bell states between different quantum pro-                     versely, it is reasonable to envision that the distributed
cessors, at least one qubit at each processor—referred to as                    quantum compiler could easily reserve—when multiple
communication qubit [30] to distinguish it from the remain-                     communication qubits are available at the same processor—
ing data qubits devoted to processing—must be reserved                          a subset of the communication qubits for computing. This
for remote interprocessor operations. Hence, a crucial trade-                   optimization task represents an interesting yet unaddressed
off between communication and data qubits arises. Specifi-                      open problem.
cally, for each remote CNOT, a Bell state is consumed [see
Fig. 4(b)] and a new Bell state must be distributed between                     2) DYNAMIC CONNECTIVITY
the remote processors through the quantum link before an-                       As mentioned in Section II-A, with single-processor quan-
other remote CNOT can be executed. Hence, the more com-                         tum computing, all the constraints on the possible interac-
munication qubits are available within a processor, the more                    tions between different qubits—arising from the underlying
remote CNOTs can be executed in parallel, reducing the over-                    physical computing architecture—can be effectively repre-
head induced by the distributed computation. But the more                       sented with a coupling map. Formally, a coupling map is a
communication qubits are available for interprocessor com-                      visual representation of the directed graph G
munication, the less valuable resources—i.e., data qubits—
are available for computing.                                                                                 G = (V, E )                              (1)
   It is unlikely that a data qubit could be dynamically turned                 where V = {vi } denotes the set of vertices representing the
into a communication qubit during the compilation, given                        qubits and E = {ei, j }vi ,v j ∈V denotes the set of directed edges

4100720                                                                                                                                    VOLUME 2, 2021

                                                                                                                      IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                                     uantum Engineering

                                                                                        Accordingly, a new Bell state must be generated and
                                                                                        distributed through the quantum link to the communi-
                                                                                        cation qubits, before a subsequent remote CNOT could
                                                                                        be executed. And even if the Bell state distribution can
                                                                                        start right after the measurements, it is reasonable to
                                                                                        assume—given the several order of magnitudes sepa-
                                                                                        rating intraprocessor qubit distance from interproces-
                                                                                        sor one—that the time needed to entangle the commu-
                                                                                        nication qubits significantly exceeds the time required
FIG. 5. Dynamic coupling map for the network topology shown in                          for local CNOTs.5 Accordingly, we have two major
Fig. 4(a). The two 5-qubit quantum processors constitute an 8-qubit                     issues. First, the “clock” of the remote operations will
virtual quantum processor with qubits interconnected through both local
and remote CNOTs. While the local CNOTs can be concurrently
                                                                                        be significantly lower than the “clock” of the local
executed—i.e., they are unconstrained—the parallel execution of multiple                operations, and hence, it becomes fundamental to min-
remote CNOTs is constrained to the availability of multiple Bell states,                imize the number of remote—rather than the number
with one Bell state for each concurrent remote CNOT. Given that only one
communication qubit is available at each processor in Fig. 4(a), out of                 of local—operations to preserve the quantum infor-
four remote CNOTs, only one can be executed at any time.                                mation integrity from decoherence (see Section II-A).
                                                                                        Furthermore, there may be periods of time—following
representing the possibility to perform4 a CNOT, with vi and                            the execution of a remote operation up to the success-
v j acting as control and target qubit, respectively.                                   ful distribution of a new Bell state—during which the
    But when it comes to distributed quantum computing, a                               quantum processors are disconnected and only local
new kind of constraints arises as a consequence of the under-                           operations are possible.
lying physical network topology.                                                    These additional constraints must be properly modeled
    More in detail, similarly to single-processor quantum                        within the coupling map, so that the distributed quantum
compiling, the remote operations are restricted to certain                       compiler can optimize the quantum circuit by accounting for
fixed pairs. Specifically, they are restricted to pairs composed                 the temporal dynamics arising with the distributed architec-
of data qubits directly connected to a communication qubit                       ture. And this represents an open problem.
within the processor coupling map. For instance, with ref-
erence to the network topology shown in Fig. 4(a), a remote                      3) AUGMENTED CONNECTIVITY
CNOT between data qubits Q2 and Q1 can be directly mapped
                                                                                 As shown in Fig. 3(b), single-processor quantum computing
onto the circuit given in Fig. 4(b). Conversely, a remote CNOT
                                                                                 must resort to either state transfer (swapping) or ancilla
between data qubits Q2 and Q4 cannot be directly executed
                                                                                 strategy to implement a CNOT between nonadjacent (within
between the pair, but it requires to distribute the operation
                                                                                 the coupling map) physical qubits. The rationale for this
through the neighbor qubits, as shown in Fig. 3(b).
                                                                                 lays in the impossibility to have direct interactions between
    However, differently from single-processor compiling, the
                                                                                 distant qubits. And the further the qubits are within the cou-
remote operations are subjects to two types of temporal
                                                                                 pling map, the longer the sequence of additional CNOTs is
constraints.
                                                                                 required, regardless of the adopted strategy.
   1) Simultaneity Limitations: As previously discussed,                            Conversely, distributed quantum computing can exploit
      each remote CNOT relies on the availability of a Bell                      a strategy—called entanglement swapping [4] and summa-
      state stored within a communication qubit. Hence,                          rized in Fig. 6—to implement a remote CNOT between qubits
      even if remote CNOTs can—in principle—be executed                          stored at remote processors, even if the processors are not
      between different remote pairs, the number of remote                       directly connected through a quantum link.
      CNOTs that can be executed simultaneously between                             In a nutshell, to distribute a Bell state between remote
      two processors is limited by the number of communi-                        processors—say quantum processor #1 and #3 in Fig. 6(a)—
      cation qubits jointly available at each processor. With                    two Bell states must be first distributed through the quantum
      reference to Fig. 5, out of four possible remote CNOTs                     links so that one Bell state is shared between the first proces-
      (denoted with blue arrows), only one can be executed                       sor and an intermediate node and another Bell state is shared
      at any time.                                                               by the same intermediate node and the second processor.
   2) Consecutiveness Limitations: Each remote CNOT con-                         Then, by performing a Bell state measurement (consisting
      sumes a Bell state as a consequence of the measure-                        of an H and a CNOT gate, followed by a joint measurement)
      ment operations on the communication qubits [21].                          on the communication qubits at the intermediate node—i.e.,
                                                                                 qubits Q0 and Q3 in Fig. 6(b)—a Bell state is obtained at
   4 In the following, for the sake of presentation, we consider the simplest    the remote communication qubits—i.e., qubits Q0 and Q3 in
binary case, i.e., either the operation can or cannot be executed. But the
discussions, as well as the results derived in the following, continue to hold
when a weight—usually representing the gate fidelity—is mapped on the               5 In the order of hundreds of nanoseconds for the IBM Yorktown quantum
edge.                                                                            processor [31].

VOLUME 2, 2021                                                                                                                                   4100720

    IEEE Transactions on
    uantum Engineering                                                        Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




FIG. 6. Augmented connectivity. Entanglement swapping increases the connectivity between physical qubits, with a number of possible remote CNOTs
that scales at least linearly with the number of processors. (a) By swapping the entanglement at the intermediate nodes—namely, quantum processor
#2—it is possible to distribute a Bell state between remote processors—namely, processors #1 and #3—even if they are not adjacent, i.e., they are not
directly connected through a quantum link. Hence, entanglement swapping enhances the network connectivity through virtual quantum links.
(b) Entanglement swapping. A Bell state can be distributed between remote processors by swapping the entanglement at an intermediate node through
local processing and classical communication. (c) Dynamic coupling map for the network topology shown in Fig. 6(a). The solid blue lines denote remote
CNOTs between adjacent processors, whereas the dotted blue lines denote remote CNOTs between distant processors achievable via entanglement
swapping.


Fig. 6(a)—by applying some local processing at the remote                       Hence, a tradeoff between “augmented connectivity” and
nodes depending on the (classical) output of the Bell state                  “EPR cost” arises with entanglement swapping, and a dis-
measurement.                                                                 tributed quantum compiler must carefully account for these
   From the above, it becomes clear that entanglement swap-                  pros and cons.
ping significantly increases the connectivity within the vir-
tual quantum processor. As an instance, qubit Q4 in Fig. 6(a)                B. RELATED WORK
can interact with just two qubits within the same processor                  Most quantum computer proposals are based on variations
via local CNOTs and two qubits within the neighbor processor                 of the nearest-neighbor, two-qubit, and concurrent execution
via remote CNOTs. However, it can interact with two more                     (NTC) architecture [32]. Depending on the layout of qubits,
qubits—i.e., Q1 and Q2 —via entanglement swapping. And                   there are three NTC architectures: 1-D, 2-D, and 3-D. The
the higher is the number of available quantum processors,                    1-D model, called linear nearest neighbor (LNN) [33], con-
the higher is the number of possible interactions. Indeed, the               sists of qubits located in a single line. In this model, only two
number of additional interactions via entanglement swapping                  neighboring qubits can interact. This is the most challenging
scales linearly with the number of available processors when                 scenario. The effects of the LNN model on performance have
only two communication qubits are available at each inter-                   been investigated for many relevant use cases, such as the
mediate processor. If this constraint is relaxed, the number                 quantum Fourier transform [34], [35], Shor’s algorithm [36],
of additional interactions via entanglement swapping scales                  [37], and adders [38].
more than linearly.                                                             Beals et al. [39] provided algorithms for efficiently mov-
   However, it must be acknowledged that the augmented                       ing and addressing quantum memory in parallel. These imply
connectivity provided by entanglement swapping does not                      that the standard circuit model can be simulated with low
come for free. Indeed, entanglement swapping consumes the                    overhead by a more realistic model of a distributed quan-
Bell states stored within the communication qubits at the                    tum computer. The authors show that for an LNN N-qubit
intermediate processors. And the higher the number of in-                    architecture, O(N) time steps are necessary for performing
termediate processors, the higher the number of consumed                     N/2 two-qubit gates in parallel. However, it is worthwhile
Bell states.                                                                 to note that the developed analysis does not consider any

4100720                                                                                                                                 VOLUME 2, 2021

                                                                                                                    IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                                   uantum Engineering




FIG. 7. Worst-case scenario in terms of overhead induced by the distributed computation: the quantum processors are interconnected through a 1-D
nearest-neighbor topology, and only one data qubit is available at each quantum processor. Intraprocessor coupling between communication qubits is
omitted for the sake of simplicity.


additional overhead induced by the compilation task, and the                calls to the costliest and most challenging task, i.e., the link
derived Big-O bound relies on linear constant that is in the                entanglement generation.
“many, many thousands” [40]. Conversely, in the following,
we develop an analysis that explicitly considers the addi-                  A. SYSTEM MODEL
tional overhead induced by the compilation task, as discussed               We consider the worst-case scenario shown in Fig. 7. More in
in Section I.                                                               detail, we assume that only one data qubit is available at each
   Zomorodi-Moghadam et al. [10] proposed a general ap-                     quantum processor.6 The rationale for this choice is as fol-
proach, based on the Kernighan–Lin algorithm for graph                      lows. Whenever multiple data qubits are available at a single
partitioning, to optimize the number of teleportations for                  quantum processor, a local CNOT can be executed between
a distributed quantum computing architecture consisting of                  these data qubits without incurring in any overhead induced
two spatially separated and long-distance quantum subsys-                   by the distributed computation. Conversely, with just one
tems. The same authors also proposed an approach based on                   data qubit available at each processor, each and every CNOT
dynamic programming [41].                                                   within the quantum circuit must be mapped into a remote
   Andrés-Martínez and Heunen [42] proposed an approach                     CNOT, and hence, the overhead induced by the distributed
that may distribute circuits across any number of quantum                   computation is the highest possible.
devices. The main idea is to turn the quantum circuit into                     Furthermore, we assume that the quantum processors are
a hypergraph and then find a partitioning that minimizes the                interconnected through a 1-D nearest-neighbor topology, as
number of cuts, as each cut corresponds to a Bell state shared              shown in Fig. 7. Again, the rationale for this choice is to
across two QPUs by means of communication qubits. The                       consider the worst-case scenario in terms of overhead in-
partitioning problem is addressed by means of the KaHyPar                   duced by the distributed computation. In fact, the considered
solver [43]. The proposed solution has some drawbacks, in                   topology is characterized by the lowest possible number of
particular that there is no way to define the number of com-                communications qubits—i.e., 2n − 2, with n denoting the
munication qubits of each QPU. In the software implementa-                  number of quantum processors—since the removal of any
tion of the algorithm, the number of available communication                communication qubit would disconnect the network into two
qubits is unlimited and cannot be constrained.                              disjoint subsets of quantum processors. And the quantum
                                                                            processors are arranged in a line—rather than in a star—to
IV. COMPILER DESIGN AND OVERHEAD BOUNDS                                     maximize both the number of nonadjacent quantum proces-
As discussed in Section III, several additional constraints                 sors and the maximum distance—in terms of hops—between
arise with the shift from single processor to distributed quan-             two nonadjacent quantum processors.
tum compiling. Given that single-processor quantum com-                        From the above, it becomes clear that the considered archi-
piling has already been proved to be NP-complete [14], it is                tecture represents the worst-case scenario in terms of over-
reasonable to expect that optimal distributed quantum com-                  head induced by the distributed computation. Hence, the ac-
piling is an even harder challenging task.                                  tual overhead induced by any real-world architecture will
   For this reason, in the following, we take a completely dif-             be always upper-bounded by the communication overhead
ferent approach. Specifically, we aim at designing a general-               induced by the considered architecture.
purpose, efficient, and effective compiler for distributed                     Clearly, we need to choose a metric for measuring the
quantum computing.                                                          overhead induced by the distributed computation. As dis-
   General-purpose because our compiler does not require                    cussed in Section II-A, there exists a general consensus on
any particular assumption on the quantum circuit to be                      circuit depth as a key performance metric of circuit compi-
compiled.                                                                   lation. Hence, in the following, we measure the overhead in
   Efficient because—as proved in Section V-A—our com-                      terms of number of additional layers required to distribute
piler is computationally efficient, exhibiting a polynomial                 the computation of a single layer in the original quantum cir-
time complexity that grows polynomially with the number                     cuit. Furthermore, we also evaluate the overhead in terms of
of logical qubits and linearly with the depth of the quantum                how many calls to the link entanglement generation process
circuit to be compiled.                                                     are required from the compiling algorithm.
   Effective because—as proved in Section IV-B—our com-                        6 Clearly, the total number of data qubits within the distributed architec-
piler assures a polynomial worst-case overhead, in terms of                 ture must be greater than the number of logical qubits within the quantum
both depth of the compiled quantum circuit and number of                    circuit to be compiled.

VOLUME 2, 2021                                                                                                                                  4100720

     IEEE Transactions on
     uantum Engineering                                                           Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




FIG. 8. Entanglement swapping strategy. Each remote CNOT in (a) requires two preliminary tasks: 1) link entanglement, for distributing the
entanglement between neighbor nodes and 2) entanglement swapping, for entangling the two remote processors involved within the CNOT. Clearly, the
swapping task is omitted whenever the CNOT operates between data qubits stored at processors that are neighbors within the network topology, as for
the ith layer. (a) Original quantum circuit. (b) Compiled quantum circuit.


B. BASIC STRATEGIES FOR DISTRIBUTING CNOTS                                        For instance, entanglement swapping—although depicted as
Let us consider a single layer of the original n-qubit quantum                    a single block—is indeed obtained with a quantum circuit
circuit. Clearly, the number of CNOTs in each layer is lower                      composed by three layers, as shown in Fig. 6(b). Similarly,
or equal to n2 , given that at most n2 gates can be executed                      the link entanglement generation requires a quantum circuit
simultaneously (and thus belong to the same layer) by oper-                       with a depth equal or greater than two, depending on the par-
ating on different pairs of qubits.                                               ticulars of the quantum technology underlying entanglement
   As discussed in Section IV-A, we aim at considering the                        generation and distribution [21].
worst-case scenario in terms of overhead induced by the dis-                         Nevertheless, the figure8 provides a clear intuition of both
tributed computing architecture. Hence, each CNOT within                          the sequentiality constraints between the different tasks and
the quantum circuit—given that it operates on physical qubits                     the parallelism achievable within each task. Specifically,
stored at different processors, as discussed in Section IV-A—                     whenever the CNOTs overlaps9 within the network topology
is a remote CNOT. As a consequence, the compiler must map                         [as for the CNOTs of the layer #i+1 in Fig. 8(a)], they must be
at most n2 remote CNOTs in each layer.                                            executed sequentially. Differently, CNOTs that do not overlap
                                                                                  [as for the CNOTs of the ith layer in Fig. 8(a)] can be ex-
1) ENTANGLEMENT-SWAPPING-BASED STRATEGY                                           ecuted simultaneously. Since we are interested in assessing
The first strategy for implementing remote CNOTs is based                         the worst-case overhead induced by distributed computation,
on the entanglement swapping technique discussed in                               in the following, we consider the worst-case scenario, in
Section III-A and shown in Fig. 6.                                                which all the CNOTs of an arbitrary layer of the quantum
   Accordingly, each remote CNOT is implemented by first                          circuit overlap within the network topology. Hence, we have
generating link entanglement [44] among neighbor nodes.                           that the depth overhead of the entanglement-swapping-based
To this aim, different techniques for entanglement genera-                        strategy does not exceed the following depth:
tion can be employed, depending on the particulars of the                                                      n
                                                                                                                  des                         (2)
underlying qubit technology [21]. Nevertheless, link entan-                                                    2
glements can be simultaneously generated, given that each                         where n denotes the number of logical qubits within the quan-
processor is equipped with two communication qubits. Once                         tum circuit and des is a constant factor (independent from the
generated, the entanglement is simultaneously7 swapped at                         characteristics of the original quantum circuit) given by
intermediate nodes so that a Bell state is distributed between
the two remote processors, and, finally, the remote CNOT is                                               des = cle + cbsm + ccx                           (3)
obtained, as shown in Fig. 4(b).
   The entanglement-swapping-based strategy is outlined in                           8 We note that—for the sake of simplicity—in Fig. 8(b), we simply

Fig. 8(b) in terms of basic tasks. Within the figure, the                         mapped the jth logical qubit Q j of layer #i in Fig. 8(a) onto the ( j + 1)th
                                                                                  processor, ignoring so any optimization achievable with a proper mapping
particulars of each task are omitted for the sake of clarity.                     of the logical qubits of the quantum circuit onto the physical qubits of the
                                                                                  quantum processor.
                                                                                     9 The term “overlap” indicates the case when the execution of the consid-
    7 In general, the capability to generate (and to regenerate, once depleted)   ered CNOTs involves overlapping sets of intermediate processors as a con-
and distribute entangled Bell states through different links in parallel de-      sequence of the constraint we imposed on the network topology of having
pends on the quantum resources available, i.e., both the number of commu-         2n − 2 communication qubits. With reference to the example in Fig. 8(a),
nication qubits at each processor and the interconnection (shared bus versus      the CNOT between Q0 and Q2 in the layer #i+1 overlaps with the CNOT
point-to-point) among the communication qubits. Differently, the possibility      between Q1 and Q4 , being the communication qubits at the processors #1
to simultaneously swap the entanglement at the intermediate nodes depends         and #2 needed to both of them. Differently, the CNOT between Q3 and Q5
only on classical resources, i.e., the possibility to simultaneously transfer     does not overlap with the CNOT between Q0 and Q2 , and hence, they can
classical information.                                                            be performed in parallel.

4100720                                                                                                                                         VOLUME 2, 2021

                                                                                                                   IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                                  uantum Engineering




FIG. 9. Data-qubit-swapping-based strategy. Swapping data qubits between remote quantum processors can be advantageous whenever the original
quantum circuit presents repetitions of the same CNOT interaction pattern, as for layers #i+1 and #i+2 in (a). Although not shown in the figure, the
entanglement swapping tasks [as in Fig. 8(b)] are needed whenever it is necessary to swap data qubits stored at processors that are not neighbors
within the network topology. (a) Original quantum circuit. (b) Compiled quantum circuit.


with cle and cbsm denoting the number of layers required                      2) DATA-QUBIT-SWAPPING-BASED STRATEGY
to perform the link entanglement task and the entanglement                    The entanglement-swapping-based strategy takes full advan-
swapping task, respectively, and ccx denoting the number                      tage of the augmented connectivity enabled by the commu-
of layers required to perform a remote CNOT once the Bell                     nication qubits—as discussed in Section III-A—to allow in-
state has been distributed between two processors. The actual                 teractions between remote processors within each layer.
values of cle , cbsm , and ccx depend on the particulars of the                   Nevertheless, whenever the original quantum circuit
underlying hardware technology.                                               presents repetitions of the same CNOT interaction pattern
   From (2), we have that the actual depth of an arbitrary                    between logical qubits—as for layers #i+1 and #i+2 in
d-depth quantum circuit compiled with the entanglement                        Fig. 9(a)—a more elaborate strategy—based on moving the
swapping based strategy will always be lower than n2 d, ne-                   data qubits—can provide better performance.
glecting the constant des . Hence, the depth overhead grows                       The strategy is shown in Fig. 9: the objective is to arrange
linearly with the number of logical qubits of the quantum                     (i.e., to swap) the data qubits within the quantum processors
circuit to be compiled. Given that this result holds for the                  so that eventually each CNOT of the original layer operates
worst-case scenario (one-data-qubit processors arranged in a                  on qubits stored at neighbor processors within the network
one-dimensional network topology), the actual depth over-                     topology.
head induced by any arbitrary distributed architecture will                       Intuitively, the strategy goal can be modeled as an array
always be upper-bounded by (2).                                               sorting problem. Indeed, similarly to classical sorting, the
   We further note that classical information must be ex-                     n data qubits (representing the values to be sorted) must be
changed between the quantum processors. For instance, the                     ordered within the network topology (representing an array
entanglement swapping task requires the transmission of                       with size equal or greater than n). However, differently from
classical information (i.e., the measurement output) through-                 classical sorting where any couple of values can be swapped
out the quantum network. Hence, in case of long-distance                      regardless from their position within the array, with the data-
quantum processors, the actual execution time of the com-                     qubit swapping, the constraints arising from the underlying
piled quantum circuit may be affected by the latency induced                  network topology must be carefully taken into account. To
by the classical communications.                                              this aim, by taking advantage of the sorting network theory,
   Finally, due to the complex and stochastic nature of                       it is easy to model the network topology constraints through
the physical mechanisms underlying quantum entangle-                          the notion of insertion network (or, equivalently, bubble net-
ment [44], several attempts can be required for establish-                    work). As a consequence, the overall depth of the equivalent
ing a link entanglement, and this may also impact the ex-                     quantum circuit grows with the number n of logical qubits
ecution time of the compiled quantum circuit. Indeed, we                      as [45]
should consider link entanglement as the critical task for
distributed quantum computation, given that the remaining                                                     2n − 3                              (4)
tasks require only local quantum operations and classical                     instead of a logarithmic log n depth factor as for classical
communications. From this perspective, the entanglement-                      sorting.
swapping-based strategy requires at most n2 repetitions of the                   Nevertheless, sorting networks—and in general classical
link entanglement task, regardless of the original quantum                    sorting—are based on the assumption that there exists a total
circuit and regardless of the characteristics of the network                  (monotonic) order over the array elements. Hence, there ex-
topology underlying the distributed computing architecture.                   ists a unique solution to the sorting problem. Conversely, the
                                                                              data-qubit-swapping-based strategy admits several equiva-
                                                                              lent solutions for the arranging problem, as exemplified in

VOLUME 2, 2021                                                                                                                               4100720

     IEEE Transactions on
    uantum Engineering                                                     Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




                                                                           swapping task, respectively, and ccx denoting the number of
                                                                           layers required to perform the remote CNOTs once the Bell
                                                                           state has been distributed between two processors.
                                                                              Proof: The proof easily follows by recognizing that: 1)
                                                                           the function SORT(·), defined in Algorithm 1, is called at
                                                                           most n4 times; and 2) after these calls to SORT(·), all the
                                                                           CNOTs, by acting on qubits stored at neighbor processors,
                                                                           can be executed at once through link entanglement followed
                                                                           by local operations, as shown in Fig. 4(b).
FIG. 10. Data-qubit-swapping-based strategy: equivalent mappings.             More specifically, in each call, we have two disjoint cases
Both (b) and (c) represent valid arrangements of the data qubits within
the remote quantum processors so that each CNOT in (a) operates on
                                                                           (line 2).
qubits stored at processors neighbor within the network topology. (a)         In the former case (lines 3–6), there exists a CNOT act-
Original quantum circuit. (b) Possible arrangement. (c) Alternative        ing within the first half portion—i.e., the first n2 logical
equivalent arrangement.
                                                                           qubits—of the original layer. Since we are considering the
                                                                           worst case—namely, a layer with n2 CNOTs—then we have
 Algorithm 1: Data-Qubit Swapping.                                         that there exists at least one CNOT acting on the last half
 Input: n-qubit circuit layer L with mod(n,4) = 0 and                      portion—i.e., the last n2 logical qubits—of the original layer.
 n
 2 CNOTs                                                                   Hence, the two CNOTs do not overlap and two simultaneous
 Output: layer L with each CNOT Operating on Neighbor                      SWAP operations can be executed—one in each half portion
 Qubits.                                                                   of the original quantum circuit—as shown here:
   1: function Sort (L)
   2:    if ∃ CNOT(qi , q j ) with i, j ≤ n2 then
   3:       //∃ CNOT(qk , ql ) with k, l > n2
   4:       Swap(qi+1 , q j )
   5:       Swap(qk+1 , ql )
                                                                           so that, within the compiled circuit—the two CNOTs act on
   6:       L = L \ {qi , qi+1 , qk , qk+1 }
                                                                           qubits stored at neighbor processors. Within the previous
   7:    else
                                                                           diagram, as well as in Algorithm 1, we omitted some minor
   8:       // ∃ CNOT(q n2 , ql ) with l > n2
                                                                           particulars for the sake of simplicity. For instance, we implic-
   9:       // and ∃ CNOT(qi , ql−1 ) with i < n/2
                                                                           itly assumed that i (and k) is odd—i.e., mod(i, 2) = 1—so
 10:        Swap(q n2 , ql−1 )
                                                                           that q j must be swapped with qi+1 . Clearly, whether i should
 11:        Swap(qi , q n2 −1 )
                                                                           be even, q j must be swapped with qi−1 .
 12:        L = L \ {q n2 −1 , q n2 , ql−1 , ql }
                                                                              In the latter case (lines 8–12), each and every CNOT acts
 13:     end if
                                                                           on two logical qubits belonging to both the half portions of
 14:     if L = ∅ then
                                                                           the original layer. Let us consider, with no lack of generality,
 15:        Sort(L)
                                                                           the CNOT acting on the n2 th logical qubit (i.e., the last qubit of
 16:     end if
                                                                           the first half portion) and let us denote as ql the second qubit
 17: end Function
                                                                           on which such a CNOT operates. Since we are considering a
                                                                           layer with n2 CNOTs, then we have that there exists a CNOT
Fig. 10. We now formalize these considerations with the                    acting on the l − 1th qubit. By denoting as qi the second qubit
following theorem.                                                         on which such a CNOT operates, it follows i < n2 . Although
   Theorem 1: Let us consider the ith layer of an arbitrary                the two CNOTs overlap, by properly selecting two SWAP
n-qubit quantum circuit. The depth of the corresponding                    operations, as shown here:
compiled quantum circuit, obtained through the data-qubit-
swapping-based strategy, does not exceed the following
depth:
                       n         
                         dqs + dqs                      (5)                we have that the SWAPs can be simultaneously executed so
                       4
                  are constant factors (independent from the
                                                                           that—within the compiled circuit—the two CNOTs act on
where dqs and dqs                                                          qubits stored at neighbor processors. Regardless of which
characteristics of the original quantum circuit) given by                  case holds, each call to the SORT (·) function compiles two
                    dqs = 3 (cle + cbsm + ccx )                      (6)   CNOTs. By recalling that at most n2 CNOTs are present in a
                     
                                                                           layer, the thesis follows.                                  
                    dqs = cle + ccx                                  (7)      From (5), we have that the actual depth of an arbitrary
with cle and cbsm denoting the number of layers required                   d-depth quantum circuit compiled with the data-qubit swap-
to perform the link entanglement task and the entanglement                 ping based strategy will always be lower than n4 d, neglecting

4100720                                                                                                                          VOLUME 2, 2021

                                                                                                                IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                               uantum Engineering

the constant factors. Hence, the depth overhead is asymptot-                  V. PERFORMANCE ANALYSIS
ically lower than the overhead induced by the entanglement-                   Here, we perform a performance analysis for the compiler
swapping-based strategy. However, an explicit comparison                      design conducted in Section IV. More in detail, in Section V-
between the two strategies depends on the particulars of the                  A, we illustrate the algorithmic implementation of the com-
underlying qubit technology through the exact expressions of                  piler, proving so its attractive feature—a polynomial time
des and dqs . Furthermore, it also depends on the repetitions                 complexity that grows quadratically with the number of log-
of the same CNOT interaction patterns within the original                     ical qubits and linearly with the depth of the quantum circuit
quantum circuit.                                                              to be compiled—from a computational perspective. Then, in
   As regards the number of repetitions of the link entangle-                 Section V-B, we validate the theoretical upper bounds on the
ment task, in general, it depends on the characteristics                      number of layers that result from compiling a layer of remote
of the underlying qubit technology, as discussed in                           CNOTs, derived in Section IV-B, against an extensive set of
Section IV-C. With reference to the IBM quantum                               medium-size quantum circuits of practical interest. Finally,
processors, where a SWAP operation is obtained through                        with Sections V-C and V-D, we conclude the performance
a sequence of three CNOTs, from (5)–(7), we have that                         analysis through an unfair—as clearly shown with Fig. 14—
the data-qubit-swapping-based strategy requires at most                       comparison with the state of the art for two different network
2n repetitions of the link entanglement task, regardless                      topologies.
of the original quantum circuit and regardless of the
characteristics of the network topology underlying the
distributed computing architecture.                                           A. COMPILER IMPLEMENTATION
                                                                              We implemented the strategies discussed in Section IV-B in
C. DISCUSSION                                                                 Python, using Qiskit [27] as the development framework.
As already mentioned above, the performance of the two                        Given a quantum circuit described in the QASM format,
strategies firmly depends on the particulars of the underlying                the compiler proceeds to instantiate a distributed architecture
                                                             
hardware technology through the parameters des , dqs , and dqs                that mimics the one described in Section IV-A. To model the
given in (3), (6), and (7).                                                   worst-case scenario depicted in Fig. 7, each QPU has one
   To better clarify this point, let us consider dqs , which                  data qubit and two communication qubits. Moreover, each
inherently denotes the cost for a SWAP operation. Having                      QPU has two neighbor QPUs, with the exception of the outer
assumed in this article the CNOT being the fundamental mul-                   QPUs that have one neighbor QPU only. Each qubit of the
tiqubit gate, a single remote SWAP operation can be obtained                  circuit is assigned to the data qubit of one QPU.
through three remote CNOTs, as in Fig. 3(b). And this is                         The compilation process is summarized and illustrated in
the rationale for the constant factor equal to 3 in (6), which                Fig. 11. Reading the circuit from left to right, the front layer,
accounts for the cost of three remote CNOTs.                                  i.e., a layer comprising only CNOT gates that can be executed
   Clearly, by changing the assumptions on the underlying                     in parallel, is updated. To this end, one-qubit gates are imme-
hardware technology, the expression of dqs changes as well.                   diately mapped to the compiled circuit, while CNOT gates
For instance, photonic technology can provide the SWAP gate                   are added to the front layer. This is done until all logical
as the native operation [46], and in such a case, dqs is equal                qubits are interested by a CNOT or there are no more CNOT
to 1. Nevertheless, the main result—i.e., (5)—continues to                    gates that can be executed in parallel in the current front layer.
hold. Furthermore, whenever the SWAP gate is the native                       Then, the front layer is compiled, rendering all currently
operation, a single CNOT can be obtained through two con-                     involved CNOT gates executable. This process is repeated
secutive SWAPs interleaved by single-qubit operations [47].                   until no more front layers can be computed, meaning that all
Hence, the expression of des must change accordingly but the                  the circuit gates have been mapped to the distributed archi-
main result—i.e., (3)—continues to hold as well.                              tecture.
   Indeed, it is worthwhile to note that, despite the differ-                    Front layer compilation is based on Algorithm 2, where
ences between the performance of the two strategies, there                    one can choose between the two strategies discussed in
exists a one-to-one mapping between the strategies. Specif-                   Section IV-B. When the entanglement-swapping-based
ically, there exists an admissible transformation allowing to                 strategy is adopted, remote CNOT gates preceded by entan-
map the compiled circuit obtained with a strategy into the                    glement swapping are applied whenever the involved QPUs
compiled circuit obtained with the other strategy. And the                    are not neighbors. Note that to perform entanglement swap-
corresponding computational task exhibits a polynomial-                       ping, as well as remote CNOTs, we need to generate link
time complexity10 for every original circuit.                                 entanglement between all involved QPUs.
                                                                                 Regarding the more advanced data-qubit-swapping-based
                                                                              strategy, the list representing the interaction between qubits
  10 Given that both the strategies exhibit a polynomial-time computational   is prepared, and then, Algorithm3 is used to compute the data
complexity, as proved in Section V-A.                                         swap operations needed to reorder the qubits. Referring to
                                                                              Fig.12(a), the list representing the interaction between qubits
                                                                              before swapping would be [112323], while the sorted list

VOLUME 2, 2021                                                                                                                          4100720

    IEEE Transactions on
    uantum Engineering                                      Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




 Algorithm 2: CompileFrontLayer.                                         add entanglement swap between e02 at qpu0 and
 Input: the Front Layer F to be Compiled, the Executed                     en2 at qpun to E
 Gates E until now                                                       add quantum teleportation between q1 and
 Output: the Executed Gates E Updated With the Com-                          en1 to E
 piled Front Layer F.                                                    add quantum teleportation between q2 and e02
     if data-qubit-swapping-based strategy then                   to E
        prepare interactions vector                                  add local swap between q1 and e02
        swaps ← SortPairs(interactions)                              add local swap between q2 and en1
        for all swap ∈ swaps do // Perform remote                  end if
      SWAPs                                                      end Function
           if two EPR pairs between QPUs then
               Teleport(swap.q1, swap.q2)
           else
                                                            after swapping would be [112233], meaning that no overlap-
               RemoteCnot(swap.q1, swap.q2)
                                                            ping CNOTs are left in the layer.
               RemoteCnot(swap.q2, swap.q1)
                                                               The data-qubit swapping routine operates on lists with a
               RemoteCnot(swap.q1, swap.q2)
                                                            number of elements—i.e., a number of logical qubits—that
           end if
                                                            is a multiple of 4. For this reason, a couple of dummy values,
        end for
                                                            set to −1, may have to be added to the end of the list when-
     end if
                                                            ever the number of CNOTs is odd. Given that the algorithm
     for all gate ∈ F do
                                                            searches for swaps form left to right, the dummy couple at the
        RemoteCnot(gate.control, gate.target)
                                                            end will be left untouched. After creating masks to keep track
     end for
                                                            of already swapped qubits, the algorithm finds all necessary
     return E
                                                            swaps in exactly n4 steps, where n is the number of elements
     function RemoteCnot(control, target)
                                                            in the list, i.e., the number of logical qubits interested by
        if control and target are not on neighboring QPUs
                                                            CNOTs.
      then
                                                               Taking into account the topology of the worst-case sce-
           qpu0 ← QPUs of control
                                                            nario shown in Fig. 7, to perform a swap, at least three remote
           qpun ← QPUs of target
                                                            CNOTs are needed. After all the data-qubit swaps have been
           for i ∈ {0, .., n − 2} do
                                                            applied, the necessary remote CNOTs have to be placed.
               add link entanglement between qpui and
                                                            Ideally, this last step would involve only remote CNOTs
                 qpui+1 to E
                                                            between neighbor QPUs, but when not all qubits of the circuit
           end for
                                                            are involved in the front layer, such as Q1 in Fig. 12(a), it may
           add entanglement swap between qpu0 and qpun
                                                            be still necessary to perform some entanglement swapping
             to E
                                                            operations, as shown in Fig. 12(b). This is because, when
        end if
                                                            sorting pairs, our algorithm does not take into account QPUs
        add link entanglement between qpu0 and qpun to E
                                                            that are not involved in the current front layer. Consequently,
        add a remote CNOT between control and target
                                                            the implementation of the data-qubit-swapping-based strat-
          to E
                                                            egy is actually a hybrid between the two strategies described
     end Function
                                                            in Section IV-B, avoiding data-qubit swapping if not neces-
     function Teleport(q1, q2)
                                                            sary and resorting instead to entanglement swapping.
        if q1 and q2 are not on neighboring QPUs then
                                                               As shown in Fig. 12, starting from the layer in
           qpu0 ← QPUs of q1
                                                            Fig. 12(a), following the data-qubit-swapping-based strat-
           qpun ← QPUs of q2
                                                            egy, in Fig. 12(b), we apply a remote SWAP between qubit 3
           for i ∈ {0, .., n − 2} do
                                                            and qubit 4, and then, we can execute all remote CNOTs in
               add link entanglement between qpui and
                                                            parallel.
                 qpui+1 to E
                                                               Moving from the topology illustrated in Fig. 7 to the one in
                  using two available EPR pairs between
                                                            Fig. 13 , we can devise a different strategy to execute swaps
                   QPUs
                                                            by exploiting the augmented connectivity, described in Algo-
           end for
                                                            rithm 2. Specifically, to perform a SWAP between QPU Qx
           e01 , e02 ← the two communication qubits
                                                            and Qy , our compiler uses one communication qubit at each
             at qpu0
                                                            QPU as a buffer memory and exploits quantum teleportation
           en1 , en2 ← the two communication qubits at
                                                            to move the state of a data qubit from Qx to Qy and vice
      qpun
                                                            versa, in parallel. After the two parallel teleportations, we
           add entanglement swap between e01 at qpu0 and
                                                            can execute two parallel local SWAPs between communica-
               en1 at qpun to E
                                                            tion qubits and data qubits at each QPU to effectively achieve

4100720                                                                                                         VOLUME 2, 2021

                                                                                                                       IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                                      uantum Engineering




FIG. 11. Workflow of the proposed compiler.




FIG. 12. Compilation of a layer with three parallel CNOTs using the sorting strategy. (a) Layer with three parallel CNOTs. (b) Layer distributed with the
Sort strategy. (c) Distributed layer after decomposing the Remote SWAP.




FIG. 13. Improving over the worst-case scenario topology. Only one data qubit is available at each quantum processor, but neighboring quantum
processors are connected with two quantum links, realized by two EPR pairs.



data qubit swapping between Qx and Qy . This is clearly                          computational complexity of O(n), with n being the number
beneficial as it only requires one layer of link entanglement                    of QPUs. Given that we need at most n/4 swaps, the compu-
generation between the interested QPUs, unlike the previous                      tational complexity of Algorithm 2 turns out to be O(n2 ). The
scenario where we needed three layers of link entanglement                       overall computational complexity of distributing a circuit is,
generation to perform three remote CNOTs.                                        therefore, O(dn2 ).
   The difference between data-qubit swapping and entan-
glement swapping lies in the fact that, if the subsequent front                  B. COMPILING OVERHEAD VALIDATION
layers are similar (in terms of CNOT interaction pattern) to                     We validate the theoretical upper bounds (derived in
the one just compiled, not much data swapping and very little                    Section IV-B) on the number of layers that result from com-
entanglement swapping (given that the front layers involve                       piling a layer of remote CNOTs, considering an extensive set
most of the qubits) will be necessary to compile those layers.                   of medium-size quantum circuits (the largest ones requiring
   Regarding the computational complexity, the compiler                          16 qubits, with the exception of a GHZ circuit, used to pro-
(whose behavior is summarized also by Algorithm 4 in                             duce Greenberger–Horne–Zeilinger states, and two random
the Appendix) reads the circuit from left to right while                         circuit with 20 qubits). Specifically, we consider quantum
updating the front layer, so its computational complexity is                     circuits that are publicly available and widely adopted for
O(d), where d is the depth of the circuit, i.e., the number                      testing quantum compilers [25], [26],11 plus a few quan-
of layers. Algorithm 2 loops through all necessary swaps                         tum chemistry circuits for the implementation of the unitary
found by Algorithm 3, and applies remote CNOTs. As we
must take into account for possible entanglement swapping
                                                                                   11 https://github.com/deeptechlabs/quantum_compiler_optim/tree/
operations between QPUs, applying a remote CNOT has a
                                                                                 master/examples

VOLUME 2, 2021                                                                                                                                     4100720

    IEEE Transactions on
    uantum Engineering                                          Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




                                                                columns show the theoretical upper bound of the depth of the
 Algorithm 3: SortPairs.
                                                                compiled CNOT layers—computed in agreement with (2)
 Input: a Vector v representing CNOT interactions be-
                                                                and (4), respectively—whereas the fifth and eighth column
 tween qubits pairs, ex. [1 2 2 3 1 3]
                                                                show the depth of the compiled CNOT layers. For comput-
 Output: the swaps to Perform.
                                                                ing the upper bound values and collecting the experimental
    // f.e.o. stands for “first element of”                     results, we set the parameters cle , cbsm , and ccx in (3), (6),
    if length(v) mod4 = 0 then // length(v) must be            and (7) as unit factors, thus obtaining des = 3, dqs = 9, and
     multiple of 4                                                 = 2.
                                                                dqs
        add {−1, −1} to v // Add a dummy pair at the end           Table 1 clearly shows that the upper bounds on the number
    end if                                                      of layers that result from compiling the layers of remote
    swaps ← ∅ // List of SWAPs to perform                       CNOTs are widely respected and hold for all the considered
    n ← length(v)                                               examples. Indeed, by comparing the actual depth with the
    mask1 ← {0, . . ., n2 − 1}                                  theoretical one, the overestimation of the bounds given in
    mask2 ← { n2 , . . ., n − 1}                                Section IV-B becomes evident. The rationale for this lays
    cycle ← 0                                                   in the number of CNOTs in each layer, which are usually
    while cycle < n/4 do                                        significantly lower than what assumed. For instance, let us
        w ← indexes of unique values in v                       consider the GHZ circuits, where each layer contains a single
        index_last ← {0, . . ., |v[mask1]|} \ w                 CNOT, and hence, the derived bounds—by assuming n/2
        if index_last = ∅ then                                  CNOTs in each layer—overestimate the depth. Nevertheless,
            swap v[mask1[end]] and                              the discrepancy can be easily fixed by substituting the n/2
               f.e.o. s.t. v[mask2] = v[mask1[end]]            factor with the actual estimation on the average number of
            update swaps                                        CNOTs in each layer with no loss of generality.
        end if
        v, mask1, swaps ← swap(v, mask1, swaps)                 C. EXPERIMENTAL RESULTS FOR THE WORST-CASE
        v, mask2, swaps ← swap(v, mask2, swaps)                 TOPOLOGY
    end while
                                                                We compared our compiler with the one proposed by Andrés-
    return swaps
                                                                Martínez and Heunen [42], in respect of which we were able
    function swap(v, mask, swaps)
                                                                to set each QPU memory to one data qubit but we could not
        w ← indexes of unique values in v
                                                                impose any limitation over the number of communication
        index_last ← f.e.o. {0, . . ., |v[mask]|} \ w
                                                                qubits per QPU nor the topology of the quantum network,
        index_ f irst ← f.e.o.v[mask] s.t. =
                                                                which is always assumed to be an hypercube. Such a topol-
     v[mask[index_last]]
                                                                ogy is shown in Fig. 14(b), where one can clearly see the
        if index_last is odd then
                                                                connectivity disparity, compared to the worst-case topology
            index_swap ← index_last − 1
                                                                illustrated in Fig. 14(a). In Figs. 15–17, the results of the
        else
                                                                comparative evaluation are plotted. For a better readability of
             index_swap ← index_last + 1
                                                                the figures, we omit data related to a 20-qubit random circuit
        end if
                                                                that presents values far greater than the rest of the dataset, for
        swap v[mask[index_swap]] and
                                                                all compiling strategies including the state of the art (such
     v[mask[index_ f irst]]
                                                                data have been included in Table 1).
        update swaps
                                                                   Fig. 15 shows the number of link generation layers, i.e., the
        remove mask[index_swap] and mask[index_last]
                                                                number of layers in the distributed circuit that comprise only
     from mask
                                                                Bell state generation and distribution between QPUs. It is
        return v, mask, swaps
                                                                clear that our compiler requires less layers of link generation
    end Function
                                                                for almost every tested circuit. Having fewer layers of link
                                                                generation reduces the time that data qubits have to spend
                                                                idle, i.e., possibly affected by decoherence, while waiting
quantum coupled cluster [48], [49] and the RYRZ heuris-         to be able to perform remote operations. Fig. 15(c) also
tic [50] wavefunction Ansätze.                                  shows that choosing the data-qubit-swapping-based strategy
   More into details, Table 1 reports a sample of the re-       against the entanglement-swapping-based strategy is gener-
sults that have been collected by compiling the circuits        ally the best choice.
with both entanglement-swapping-based and data-qubit-              Regarding the depth of the distributed circuits, illus-
swapping-based strategies. Within the table, the first column   trated in Fig. 16, we can see that for some circuits,
shows the name of the circuit and the second column shows       our compiler clearly outperforms Andrés-Martínez’s one.
the number n of logical qubits within the circuit. The third    Fig. 16(c) confirms that the data-qubit-swapping-based
column shows the number of CNOT layers in the original          strategy is better than the entanglement-swapping-based
circuit—i.e., the uncompiled circuit. The fourth and seventh    one.

4100720                                                                                                              VOLUME 2, 2021

                                                                                                                        IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                                       uantum Engineering

TABLE 1. Validation of the theoretical upper bounds derived in Section IV-B against a heterogeneous set of quantum circuits each circuit is
characterized by a number of qubits n and a number of CNOT layers, i.e., layers that comprise only CNOT gates. For each compiling strategy, there is a
theoretical upper bound on the number of layers that are necessary to realize the remote CNOTs and an actual number of layers resulting from the
compilation process. The ratio between the latter and the former is also reported




FIG. 14. Comparison of the worst-case scenario LNN topology with the hypercube topology assumed by the compiler proposed by Andrés-Martínez and
Heunen [42]. As shown in (a), for n = 16 QPUs, the longest path between two QPUs consists of n − 1 = 15 links, while with the hypercube topology in
(b) is only about log2 n = 3 links. (a) LNN topology. (b) Hypercube topology.




FIG. 15. Comparing the entanglement-swapping-based and data-qubit-swapping-based strategies of our compiler with Andrés-Martínez’s
compiler [42], in terms of link entanglement generation layers. Our compiler distributes circuits on the worst-case topology, with only one link between
neighboring QPUs (illustrated in Fig. 7), while Andrés-Martínez’s one exploits a more favorable topology, i.e., the hypercube illustrated in Fig. 14(b). Both
topologies are characterized by one data qubit per QPU.


VOLUME 2, 2021                                                                                                                                      4100720

     IEEE Transactions on
     uantum Engineering                                                            Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




FIG. 16. Comparing the entanglement-swapping-based and data-qubit-swapping-based strategies of our compiler with Andrés-Martínez’s
compiler [42], in terms of circuit depth. Our compiler distributes circuits on the worst-case topology, with only one link between neighboring QPUs
(illustrated in Fig. 7), while Andrés-Martínez’s one exploits a more favorable topology, i.e., the hypercube illustrated in Fig. 14(b). Both topologies are
characterized by one data qubit per QPU.




FIG. 17. Comparing the entanglement-swapping-based and data-qubit-swapping-based strategies of our compiler with Andrés-Martínez’s
compiler [42], in terms of consumed EPR pairs. Our compiler distributes circuits on the worst-case topology, with only one link between neighboring
QPUs (illustrated in Fig. 7), while Andrés-Martínez’s one exploits a more favorable topology, i.e., the hypercube illustrated in Fig. 14(b). Both topologies
are characterized by one data qubit per QPU.




FIG. 18. Comparing the entanglement-swapping-based and data-qubit-swapping-based strategies of our compiler with Andrés-Martínez’s
compiler [42] over link entanglement generation layers. Our compiler distributed circuits on the topology illustrated in Fig. 13, with two links between
neighboring QPUs (illustrated in Fig. 7), while Andrés-Martínez’s one exploits a more favorable topology, i.e., the hypercube illustrated in Fig. 14(b). Both
topologies are characterized by one data qubit per QPU.




4100720                                                                                                                                        VOLUME 2, 2021

                                                                                                                        IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                                       uantum Engineering




FIG. 19. Comparing the entanglement-swapping-based and data-qubit-swapping-based strategies of our compiler with Andrés-Martínez’s
compiler [42], in terms of circuits’ depth. Our compiler distributed circuits on the topology illustrated in Fig. 13, with two links between neighboring
QPUs (illustrated in Fig. 7), while Andrés-Martínez’s one exploits a more favorable topology, i.e., the hypercube illustrated in Fig. 14(b). Both topologies
are characterized by one data qubit per QPU.




   With respect to the number of generated Bell states, de-                      neighbor QPUs. As described in Section V-A, this setting
picted in Fig. 17, it can be observed that our compiler con-                     enables our compiler to perform data-qubit swapping in a
sumes a fair amount of Bell states compared to Andrés-                           more efficient way and also greatly reduces the number of
Martínez’s compiler. This was expected, and it is mostly due                     layers dedicated to the link entanglement generation, as we
to the fact that Andrés-Martínez’s compiler benefits from a                      can generate and use double the number of links in parallel.
hypercube network topology, as showed in Fig. 14(b). Us-                         Such a performance improvement is clearly shown in Fig. 18.
ing such a topology means that, in most cases, a link be-                           The same considerations apply to the depth of the com-
tween two QPUs can be directly generated with just one                           piled circuits, illustrated in Fig. 19, where we can observe
Bell state, which is in direct contrast with the worst-case                      an appreciable improvement against the worst-case scenario
topology that we used, depicted in Fig. 14(a). In our linear                     and the state-of-the-art compiler. As for the number of gener-
topology, to generate a link between two nonneighboring                          ated EPR pairs rendered in Fig. 20, aside from an impercep-
QPUs, we need to perform entanglement swapping, gen-                             tible difference with the worst-case scenario, the advantage
erating, and consuming Bell states shared by all the oth-                        of an hypercube topology is still evident.
ers QPUs in between. Nevertheless, the time needed to
generate one Bell state should be the same as to gener-
ate n Bell states in parallel, and with Fig. 15, we already                      VI. CONCLUSION
showed that our compiler usually needs fewer layers of link                      In this article, we have discussed the main challenges aris-
generation.                                                                      ing with compiler design for distributed quantum comput-
   It is worthwhile to note that with network topologies                         ing. Then, we analytically derived an upper bound of the
different from the considered one—namely, the worst-case                         overhead induced by quantum compilation for distributed
topology where each CNOT must be mapped into a remote                            quantum computing. The derived bound accounts for the
CNOT—new optimization challenges arise. As instance,                             overhead induced by the underlying computing architecture
whenever multiple data qubits are available at each (or some                     as well as the additional overhead induced by the suboptimal
nodes), only a subset of CNOTs must be mapped into remote                        quantum compiler. To this aim, we designed a quantum com-
operations. Hence, the compiler should be able to optimize                       piler with three key features: 1) general-purpose, namely,
choices such as which subcircuit should be mapped to which                       requiring no particular assumptions on the quantum circuits
node or which CNOT should be performed via communica-                            to be compiled; 2) efficient, namely, exhibiting a polynomial-
tion qubits. Clearly, the optimal strategies—as well as the                      time computational complexity so that it can successfully
metrics to measure the optimality of a strategy—represents                       compile medium-to-large circuits of practical value; and 3)
interesting open problems.                                                       effective, being the total circuit depth overhead induced by
                                                                                 the quantum circuit compilation always upper-bounded by a
D. ADDITIONAL EXPERIMENTAL RESULTS                                               factor that grows linearly with the number of logical qubits of
To show that the proposed compiling strategies can be ap-                        the original quantum circuit. We validated the theoretical up-
plied to more complex topologies, we tested them on a slight                     per bound against an extensive set of medium-size quantum
variation of the worst-case scenario. This new topology is de-                   circuits of practical interest, and we confirmed the validity
picted in Fig. 13, where we doubled the number of EPR pairs                      of the compiler design through an extensive performance
per QPU; hence, we doubled the number of links between                           analysis.

VOLUME 2, 2021                                                                                                                                      4100720

     IEEE Transactions on
     uantum Engineering                                                           Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




FIG. 20. Comparing the entanglement-swapping-based and data-qubit-swapping-based strategies of our compiler with Andrés-Martínez’s
compiler [42] over consumed EPR pairs. Our compiler distributed circuits on the topology illustrated in Fig. 13, with two links between neighboring
QPUs (illustrated in Fig. 7), while Andrés-Martínez’s one exploits a more favorable topology, i.e., the hypercube illustrated in Fig. 14(b). Both topologies
are characterized by one data qubit per QPU.



 Algorithm 4: Compile.                                                             Algorithm 5: UpdateFrontLayer.
 Input: the circuit to be Compiled                                                 Input: G Gates to be Executed, E Executed Gates Until
 Output: the Compiled Circuit.                                                     Now
    G ← all gates from circuit                                                     Output: Updated G, Updated E, New Front Layer F.
    E ← ∅ // executed gates                                                           A ← ∅ // allocated qubits
    create new_circuit as an empty circuit                                            F ← ∅ // new front layer
    while G = ∅ do                                                                   R ← ∅ // gates to remove
       G, F, E ← UpdateFrontLayer(G, E) // F is the                                   width ← total number of data qubits available
     front layer                                                                      for all gate ∈ G do
       if F = ∅ then                                                                   if |A| = width then
          E ← CompileFrontLayer(F, E)                                                      break
       end if                                                                           end if
    end while                                                                           if A ∩ gate.qubits = ∅ then
    for all gate ∈ E do :                                                                  if gate is a one-qubit gate then
       add gate to new_circuit                                                                add gate to E
    end for                                                                                else
    return new_circuit                                                                        add gate to F
                                                                                              add gate to E
APPENDIX                                                                                      add gate.qubits to A
Here, we present a pseudocode description of the whole                                     end if
compilation process illustrated in Fig. 11 and summarized                                  add gate to R
by Algorithm 4. The front layer is iteratively updated with                             else:
Algorithm 5 and compiled by Algorithm 2. This is done                                      add gate.qubits to A
until no more front layers can be computed, meaning that                                end if
all gates have been mapped and the compilation process has                            end for
finished.                                                                             for all gate ∈ R do
                                                                                        remove gate from G
ACKNOWLEDGMENT                                                                        end for
This article benefited from the High Performance Computing                            return G, F, E
facility of the University of Parma, Parma, Italy. The authors
would like to thank Pablo Andrés-Martínez for answering
questions about his related work.
                                                                                  [2] M. Caleffi, A. S. Cacciapuoti, and G. Bianchi, “Quantum Inter-
                                                                                      net: From communication to distributed computing!” in Proc. 5th
REFERENCES                                                                            ACM Int. Conf. Nanoscale Comput. Commun., 2018, Art. no. 3,
 [1] A. S. Cacciapuoti, M. Caleffi, F. Tafuri, F. S. Cataliotti, S. Gherar-           doi: 10.1145/3233188.3233224.
     dini, and G. Bianchi, “Quantum Internet: Networking challenges in dis-       [3] M. Caleffi, D. Chandra, D. Cuomo, S. Hassanpour, and A. S. Cacciapuoti,
     tributed quantum computing,” IEEE Netw., vol. 34, no. 1, pp. 137–143,            “The rise of the quantum Internet,” Computer, vol. 53, no. 6, pp. 67–72,
     Jan./Feb. 2020, doi: 10.1109/MNET.001.1900092.                                   2020, doi: 10.1109/MC.2020.2984871.


4100720                                                                                                                                        VOLUME 2, 2021

                                                                                                                            IEEE Transactions on
Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING                                                           uantum Engineering

 [4] R. V. Meter and S. J. Devitt, “The path to scalable distributed quan-        [28] D. Ferrari and M. Amoretti, “Efficient and effective quantum com-
     tum computing,” Computer, vol. 49, no. 9, pp. 31–42, Sep. 2016,                   piling for entanglement-based machine learning on IBM Q devices,”
     doi: 10.1109/MC.2016.291.                                                         Int. J. Quantum Inf., vol. 16, no. 08, 2018, Art. no. 1840006,
 [5] S. Pirandola and S. L. Braunstein, “Physics: Unite to build a quan-               doi: 10.1142/S0219749918400063.
     tum internet,” Nature, vol. 532, no. 7598, pp. 169–171, Apr. 2016,           [29] L. Cincio, Y. Subaşı, A. T. Sornborger, and P. J. Coles, “Learning the quan-
     doi: 10.1038/532169a.                                                             tum algorithm for state overlap,” New J. Phys., vol. 20, no. 11, Nov. 2018,
 [6] E. Gibney, “Chinese satellite is one giant step for the quantum Internet,”        Art. no. 113022, doi: 10.1088/1367-2630/aae94a.
     Nature, vol. 535, no. 7613, pp. 478–479, Jul. 2016, doi: 10.1038/535478a.    [30] W. Kozlowski, S. Wehner, R. Van Meter, B. Rijsman, A. S. Cacciapuoti,
 [7] W. D, R. Lamprecht, and S. Heusler, “Towards a quantum Internet,” Eur.            and M. Caleffi, “Architectural principles for a quantum internet,” Inter-
     J. Phys., vol. 38, no. 4, May 2017, Art. no. 043001, doi: 10.1088/1361-           net Engineering Task Force, Internet-Draft draft-irtf-qirg-principles-03,
     6404/aa6df7.                                                                      Mar. 2020.
 [8] C. Simon, “Towards a global quantum network,” Nat. Photon., vol. 11,         [31] N. M. Linke et al., “Experimental comparison of two quantum computing
     no. 11, pp. 678–680, 2017, doi: 10.1038/s41566-017-0032-0.                        architectures,” Proc. Nat. Acad. Sci., vol. 114, no. 13, pp. 3305–3310,
 [9] S. Wehner, D. Elkouss, and R. Hanson, “Quantum internet: A vision for             2017, doi: 10.1073/pnas.1618020114.
     the road ahead,” Science, vol. 362, no. 6412, 2018, Art. no. eaam9288,       [32] R. Van Meter and K. M. Itoh, “Fast quantum modular expo-
     doi: 10.1126/science.aam9288.                                                     nentiation,” Phys. Rev. A, vol. 71, May 2005, Art. no. 052320,
[10] M. Zomorodi-Moghadam, M. Houshmand, and M. Houshmand, “Opti-                      doi: 10.1103/PhysRevA.71.052320.
     mizing teleportation cost in distributed quantum circuits,” Int. J. Theor.   [33] A. G. Fowler, S. J. Devitt, and L. C. L. Hollenberg, “Implementation of
     Phys., vol. 57, pp. 848–861, 2018, doi: 10.1007/s10773-017-3618-x.                SHOR’s algorithm on a linear nearest neighbor qubit array,” Quantum Inf.
[11] L. Gyongyosi and S. Imre, “Entanglement concentration service for                 Comput., vol. 4, pp. 237–251, 2004, doi: 10.5555/2011827.2011828.
     the quantum Internet,” Quantum Inf. Process., vol. 19, no. 8, 2020,          [34] Y. Takahashi, N. Kunihiro, and K. Ohta, “The quantum Fourier transform
     Art. no. 221, doi: 10.1007/s11128-020-02716-3.                                    on a linear nearest neighbor architecture,” Quantum Inf. Comp., vol. 7,
[12] L. Gyongyosi and S. Imre, “Routing space exploration for scalable routing         pp. 383–391, 2007, doi: 10.5555/2011725.2011732.
     in the quantum Internet,” Sci. Rep., vol. 10, no. 1, 2020, Art. no. 11874,   [35] R. Van Meter, “Communications topology and distribution of the quantum
     doi: 10.1038/s41598-020-68354-y.                                                  Fourier transform,” in Proc. Quantum Inf. Technol. Symp., 2004.
[13] D. Cuomo, M. Caleffi, and A. S. Cacciapuoti, “Towards a distributed          [36] S. A. Kutin, “Shor’s algorithm on a nearest-neighbor machine,” 2007,
     quantum computing ecosystem,” IET Quantum Commun., vol. 1, pp. 3–8,               arXiv:quant-ph/0609001.
     Jul. 2020, doi: 10.1049/iet-qtc.2020.0002.                                   [37] R. Van Meter, W. J. Munro, K. Nemoto, and K. M. Itoh, “Arith-
[14] A. Botea, A. Kishimoto, and R. Marinescu, “On the complexity of quan-             metic on a distributed-memory quantum multicomputer,” ACM J.
     tum circuit compilation,” in Proc. Symp. Combinatorial Search, 2018,              Emerg. Technol. Comput. Syst., vol. 3, no. 4, Jan. 2008, Art. no. 2,
     pp. 138–142.                                                                      doi: 10.1145/1324177.1324179.
[15] E. G. Rieffel and W. H. Polak, Quantum Computing: A Gentle Introduc-         [38] B.-S. Choi and R. Van Meter, “On the effect of quantum interaction dis-
     tion, Cambridge, MA, USA: MIT Press, 2011, doi: 10.5555/1973124.                  tance on quantum addition circuits,” J. Emerg. Technol. Comput. Syst.,
[16] M. A. Nielsen and I. L. Chuang, Quantum Computation and Quan-                     vol. 7, no. 3, 2011, Art. no. 11, doi: 10.1145/2000502.2000504.
     tum Information, Cambridge, U.K.: Cambridge Univ. Press, 2010,               [39] R. Beals et al., “Efficient distributed quantum computing,” Proc. Roy. Soc.
     doi: 10.1017/CBO9780511976667.                                                    A, Math., Phys. Eng. Sci., vol. 469, no. 2153, 2013,Art. no. 20120686,
[17] D. Deutsch, “Quantum theory, the Church-Turing principle and the uni-             doi: 10.1098/rspa.2012.0686.
     versal quantum computer,” Proc. Roy. Soc. London A, Math., Phys. Eng.        [40] T. H. Cormen, C. E. Leiserson, R. L. Rivest, and C. Stein, Introduction to
     Sci., vol. 400, pp. 97–117, 1985, doi: 10.1098/rspa.1985.0070.                    Algorithms, 2nd ed. Cambridge, MA: USA: MIT Press, 2001.
[18] S. Boixo, “Characterizing quantum supremacy in near-term devices,”           [41] Z. Davarzani, M. Zomorodi-Moghadam, M. Houshmand, and M. Nouri-
     Nat. Phys., vol. 14, no. 6, pp. 595–600, 2018, doi: 10.1038/s41567-018-           Baygi, “A dynamic programming approach for distributing quantum
     0124-x.                                                                           circuits by bipartite graphs,” Quantum Inf. Process., vol. 19, 2020,
[19] A. Kandala, K. Temme, A. D. Crcoles, A. Mezzacapo, J. M. Chow, and                Art. no. 360, doi: 10.1007/s11128-020-02871-7.
     J. M. Gambetta, “Error mitigation extends the computational reach of a       [42] P. Andrés-Martínez and C. Heunen, “Automated distribution of quantum
     noisy quantum processor,” Nature, vol. 567, no. 7749, pp. 491–495, 2019,          circuits via hypergraph partitioning,” Phys. Rev. A, vol. 100, Sep. 2019,
     doi: 10.1038/s41586-019-1040-7.                                                   Art. no. 032308, doi: 10.1103/PhysRevA.100.032308.
[20] L. Gyongyosi and S. Imre, “Circuit depth reduction for gate-model            [43] Y. Akhremtsev, T. Heuer, P. Sanders, and S. Schlag, “Engineering a direct
     quantum computers,” Sci. Rep., vol. 10, no. 1, 2020, Art. no. 11229,              k-way hypergraph partitioning algorithm,” in Proc. Meeting Algorithm
     doi: 10.1038/s41598-020-67014-5.                                                  Eng. Exp., 2017, pp. 28–42, doi: 10.1137/1.9781611974768.3.
[21] A. S. Cacciapuoti, M. Caleffi, R. Van Meter, and L. Hanzo, “When entan-      [44] M. Caleffi, “Optimal routing for quantum networks,” IEEE Access, vol. 5,
     glement meets classical communications: Quantum teleportation for the             pp. 22 299–22 312, 2017, doi: 10.1109/ACCESS.2017.2763325.
     quantum internet,” IEEE Trans. Commun., vol. 68, no. 6, pp. 3808–3833,       [45] D. E. Knuth, The Art of Computer Programming: Sorting and Search-
     Jun. 2020, doi: 10.1109/TCOMM.2020.2978071.                                       ing. vol. 3, 2nd ed. Boston, MA, USA: Addison Wesley Longman,
[22] IBM, IBM quantum systems, 2020. [Online]. Available: https://quantum-             1998.
     computing.ibm.com/docs/cloud/backends/systems/system-backends-               [46] T. Ono, R. Okamoto, M. Tanida, H. F. Hofmann, and S. Takeuchi, “Im-
     systems-available                                                                 plementation of a quantum controlled-SWAP gate with photonic circuits,”
[23] J. C. Garcia-Escartin and P. Chamorro-Posada, “Equivalent quantum cir-            Sci. Rep., vol. 7, no. 1, 2017, Art. no. 45353, doi: 10.1038/srep45353.
     cuits,” 2011, arXiv:1110.2998.                                               [47] N. Schuch and J. Siewert, “Natural two-qubit gate for quantum com-
[24] A. D. Crcoles et al., “Challenges and opportunities of near-term quan-            putation using the XY interaction,” Phys. Rev., vol. 67, Mar. 2003,
     tum computing systems,” Proc. IEEE, vol. 108, no. 8, pp. 1338–1352,               Art. no. 032301, doi: 10.1103/PhysRevA.67.032301.
     Aug. 2020, doi: 10.1109/JPROC.2019.2954005.                                  [48] A. Peruzzo et al., “A variational eigenvalue solver on a photonic
[25] A. Zulehner, A. Paler, and R. Wille, “An efficient methodology for                quantum processor,” Nat. Commun., vol. 5, 2014, Art. no. 4213,
     mapping quantum circuits to the IBM QX architectures,” IEEE Trans.                doi: 10.1038/ncomms5213.
     Comput.-Aided Des. Integr. Circuits Syst., vol. 38, no. 7, pp. 1226–1236,    [49] P. K. Barkoutsos et al., “Quantum algorithms for electronic struc-
     Jul. 2019, doi: 10.1109/TCAD.2018.2846658.                                        ture calculations: Particle-hole Hamiltonian and optimized wave-function
[26] G. Li, Y. Ding, and Y. Xie, “Tackling the qubit mapping problem for NISQ-         expansions,” Phys. Rev. A, vol. 98, Aug. 2018, Art. no. 022322,
     era quantum devices,” in Proc. Int. Conf. Archit. Support Program. Lang.          doi: 10.1103/PhysRevA.98.022322.
     Oper. Syst., 2019, pp. 1001–1014, doi: 10.1145/3297858.3304023.              [50] A. Kandala et al., “Hardware-efficient variational quantum eigensolver
[27] Qiskit: An Open-Source Framework for Quantum Computing, IBM,                      for small molecules and quantum magnets,” Nature, vol. 549, no. 7671,
     Armonk, NY, USA, 2019.                                                            pp. 242–246, Sep. 2017, doi: 10.1038/nature23879.




VOLUME 2, 2021                                                                                                                                            4100720

     IEEE Transactions on
     uantum Engineering                                                          Ferrari et al.: COMPILER DESIGN FOR DISTRIBUTED QUANTUM COMPUTING




                           Davide Ferrari (Graduate Student Member,                                      Michele Amoretti (Senior Member, IEEE) re-
                           IEEE) received the B.Sc. degree in computer en-                               ceived the Ph.D. degree in information technolo-
                           gineering from the Polytechnic of Milan, Milan,                               gies from the University of Parma, Parma, Italy,
                           Italy, in 2016, and the M.Sc. degree in computer                              in 2006.
                           engineering from the University of Parma, Parma,                                 He is currently an Associate Professor of Com-
                           Italy, in 2019, where he is currently working to-                             puter Engineering with the University of Parma.
                           ward the Ph.D. degree with the Department of                                  In 2013, he was a Visiting Researcher with LIG
                           Engineering and Architecture.                                                 Lab, Grenoble, France. He authored or coau-
                              He has been a Research Scholar with the Future                             thored more than 100 research papers in refer-
                           Technology Laboratory, University of Parma,                                   eed international journals, conference proceed-
                           working on the design of efficient algorithms for                             ings, and books. He is involved in the Quantum
quantum compiling. He is involved in the Quantum Information Science            Information Science research and teaching initiative with the University
research initiative with the University of Parma, where he is a member of       of Parma, where he leads the Quantum Software research unit. He is the
the Quantum Software research unit. His research interests include efficient    CINI Consortium delegate in the CEN-CENELEC Focus Group on Quan-
quantum compiling for quantum simulations and quantum machine learn-            tum Technologies. His current research interests include high-performance
ing.                                                                            computing, quantum computing, and the Internet of Things.
   Mr. Ferrari won the IBM Quantum Awards Circuit Optimization Devel-              Dr. Amoretti is an Associate Editor for the IEEE Transactions on
oper Challenge, in 2020.                                                        Quantum Engineering and the International Journal of Distributed Sen-
                                                                                sor Networks.

                           Angela Sara Cacciapuoti (Senior Member,
                           IEEE) received the “Laurea” (integrated                                          Marcello Caleffi (Senior Member, IEEE) re-
                           B.S./M.S.) (summa cum laude) degree in                                           ceived the M.S. degree (summa cum laude) in
                           telecommunications engineering and the Ph.D.                                     computer science engineering from the Univer-
                           degree in electronic and telecommunications                                      sity of Lecce, Lecce, Italy, in 2005, and the Ph.D.
                           engineering from the University of Naples                                        degree in electronic and telecommunications en-
                           Federico II, Naples, Italy, in 2005 and 2009,                                    gineering from the University of Naples Federico
                           respectively.                                                                    II, Naples, Italy, in 2009.
                              She is currently an Associate Professor with                                     He is currently an Associate Professor with the
                           the University of Naples Federico II. She was a                                  Department of Electrical Engineering and Infor-
                           Visiting Researcher with the Georgia Institute                                   mation Technology, University of Naples Fed-
of Technology, Atlanta, GA, USA, and the Universitat Politecnica de                                         erico II. From 2010 to 2011, he was a Visiting
Catalunya, Barcelona, Spain. Since July 2018, she has held the national         Researcher with the Broadband Wireless Networking Laboratory, Georgia
habilitation as a Full Professor in Telecommunications Engineering. Her         Institute of Technology, Atlanta, GA, USA. In 2011, he was also a Visit-
work has appeared in first-tier IEEE journals. Her current research interests   ing Researcher with the NaNoNetworking Center in Catalunya, Universitat
include quantum communications, quantum networks, and quantum                   Politecnica de Catalunya, Barcelona, Spain. Since July 2018, he has held
information processing.                                                         the Italian national habilitation as a Full Professor in Telecommunications
   Dr. Cacciapuoti is an Area Editor for the IEEE Communications                Engineering. His work appeared in several premier IEEE transactions and
Letters and an Editor/Associate Editor for the IEEE Transactions                journals.
on Communications, the IEEE Transactions on Wireless Commu-                        Dr. Caleffi received multiple awards, including Best Strategy Award, Most
nications, the IEEE Transaction on Quantum Engineering, the                     Downloaded Article Awards, and Most Cited Article Awards. He is an
IEEE Network, and the IEEE Open Journal of the Communications                   Associate Technical Editor for the IEEE Communications Magazine and an
Society. She has received various awards. She was a recipient of the            Associate Editor for the IEEE Transactions on Quantum Engineering
2017 Exemplary Editor Award of the IEEE Communications Letters. In              and the IEEE Communications Letters. He served as Chair, Technical
2016, she was an appointed member of the IEEE Communications Society            Program Committee (TPC) Chair, Session Chair, and TPC Member for
(ComSoc) Young Professionals Standing Committee. From 2017 to 2018,             several premier IEEE Conferences. In 2017, he became a Distinguished
she was the Award Co-Chair of the N2Women Board. From 2017 to 2020,             Lecturer for the IEEE Computer Society. In December 2017, he has been
she was the Treasurer of the IEEE Women in Engineering Affinity Group           elected Treasurer of the Joint IEEE Vehicular Technology Society/IEEE
of the IEEE Italy Section. In 2018, she was appointed as the Publicity Chair    Communications Society Chapter Italy Section. In December 2018, he was
of the IEEE ComSoc Women in Communications Engineering (WICE)                   appointed a Member of the IEEE New Initiatives Committee.
Standing Committee. Since 2020, she has been the Vice-Chair of WICE.




4100720                                                                                                                                        VOLUME 2, 2021
