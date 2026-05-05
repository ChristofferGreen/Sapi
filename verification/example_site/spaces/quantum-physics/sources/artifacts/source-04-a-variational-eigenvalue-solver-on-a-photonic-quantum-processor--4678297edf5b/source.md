# 04-a-variational-eigenvalue-solver-on-a-photonic-quantum-processor

ARTICLE
Received 9 Dec 2013 | Accepted 27 May 2014 | Published 23 Jul 2014                          DOI: 10.1038/ncomms5213              OPEN

A variational eigenvalue solver on a photonic
quantum processor
Alberto Peruzzo1,*,w, Jarrod McClean2,*, Peter Shadbolt1, Man-Hong Yung2,3, Xiao-Qi Zhou1, Peter J. Love4,
Alán Aspuru-Guzik2 & Jeremy L. O’Brien1



Quantum computers promise to efﬁciently solve important problems that are intractable on a
conventional computer. For quantum systems, where the physical dimension grows expo-
nentially, ﬁnding the eigenvalues of certain operators is one such intractable problem and
remains a fundamental challenge. The quantum phase estimation algorithm efﬁciently ﬁnds
the eigenvalue of a given eigenvector but requires fully coherent evolution. Here we present
an alternative approach that greatly reduces the requirements for coherent evolution and
combine this method with a new approach to state preparation based on ansätze and
classical optimization. We implement the algorithm by combining a highly reconﬁgurable
photonic quantum processor with a conventional computer. We experimentally demonstrate
the feasibility of this approach with an example from quantum chemistry—calculating the
ground-state molecular energy for He–H þ . The proposed approach drastically reduces the
coherence time requirements, enhancing the potential of quantum resources available today
and in the near future.




1 Centre for Quantum Photonics, H.H. Wills Physics Laboratory & Department of Electrical and Electronic Engineering, University of Bristol, Bristol BS8 1UB,

UK. 2 Department of Chemistry and Chemical Biology, Harvard University, Cambridge, Massachusetts 02138, USA. 3 Center for Quantum Information,
Institute for Interdisciplinary Information Sciences,Tsinghua University, Beijing 100084, P. R. China. 4 Department of Physics, Haverford College, Haverford,
Pennsylvania 19041, USA. * These authors contributed equally to this work. w Present address: School of Physics, University of Sydney, Sydney, New South
Wales 2006, Australia. Correspondence and requests for materials should be addressed to A.P. (email: Alberto.Peruzzo@sydney.edu.au) or to A.A.-G.
(email: Aspuru@chemistry.harvard.edu) or to J.L.O’B. (email: Jeremy.obrien@bristol.ac.uk).

NATURE COMMUNICATIONS | 5:4213 | DOI: 10.1038/ncomms5213 | www.nature.com/naturecommunications                                                             1
                                                & 2014 Macmillan Publishers Limited. All rights reserved.

ARTICLE                                                                                NATURE COMMUNICATIONS | DOI: 10.1038/ncomms5213




I
    n chemistry, the properties of atoms and molecules can be           including the electronic structure Hamiltonian of quantum
    determined by solving the Schrödinger equation. However,           chemistry, the quantum Ising Model, the Heisenberg Model20,21,
    because the dimension of the problem grows exponentially            matrices that are well approximated as a sum of n-fold tensor
with the size of the physical system under consideration, exact         products22,23, and more generally any k-sparse Hamiltonian
treatment of these problems remains classically infeasible for          without evident tensor product structure (see Supplementary
compounds with more than 2–3 atoms1. Many approximate                   Methods for details). Thus, the evaluation of /HS reduces to the
methods2 have been developed to treat these systems, but                sum of a polynomial number of expectation values of simple Pauli
efﬁcient, exact methods for large chemical problems remain out          operators for a quantum state |cS, multiplied by some real
of reach for classical computers. Beyond chemistry, the solution        constants. A quantum device can efﬁciently evaluate the
of large eigenvalue problems3 would have applications ranging           expectation value of a tensor product of an arbitrary number of
from determining the results of internet search engines4 to             simple Pauli operators23. Therefore, with an n-qubit state we can
designing new materials and drugs5.                                     efﬁciently evaluate the expectation value of this 2n  2n
   Recent developments in the ﬁeld of quantum computation               Hamiltonian.
offer a way forward for determining efﬁcient solutions of many             One might attempt this using a classical computer by
instances of large eigenvalue problems that are classically             separately optimizing all reduced states corresponding to the
intractable6–12. Quantum approaches to ﬁnding eigenvalues               desired terms in the Hamiltonian, but this would suffer from the
have previously relied on the quantum phase estimation (QPE)            N-representability problem, which is known to be intractable for
algorithm. The QPE algorithm offers an exponential speedup              both classical and quantum computers (it is in the quantum
over classical methods and requires a number of quantum opera-          complexity class QMA-Hard24). The power of our approach
tions O(p  1) to obtain an estimate with precision p (refs 13–18).     derives from the fact that quantum hardware can store a global
In the standard formulation of QPE, one assumes the eigenvector         quantum state with exponentially fewer resources than required
|cS of a Hermitian operator H is given as input and the problem         by classical hardware, and as a result the N-representability
is to determine the corresponding eigenvalue l. The time the            problem does not arise.
quantum computer must remain coherent is determined by the                 The expectation value of a tensor product of an arbitrary
necessity of O(p  1) successive applications of e  iHt, each of       number of Pauli operators can be estimated by local measure-
which can require on the order of millions or billions of quantum       ment of each qubit6. Such independent measurements can be
gates for practical applications17,19, as compared to the tens to       performed in parallel, incurring a constant cost in time.
hundreds of gates achievable in the short term.                         Furthermore, since these operators are normalized and ﬁnite-
   Here we introduce an alternative to QPE that signiﬁcantly            dimensional, their spectra are bounded. As a result, each
                                                                                   ij ...        j
reduces the requirements for coherent evolution. We have                hHim i ¼ hab ... hsia  sb . . . i can be estimated to a precision p of
developed a reconﬁgurable quantum processing unit (QPU),                an individual element with coefﬁcient h, which is an arbitrary
                                                                                                                         ij:::
which efﬁciently calculates the expectation value of a                  element from the set of constants fhab::: g, at a cost of
Hamiltonian (H), providing an exponential speedup over                           2         2
                                                                        O(|hmax| Mp ) repetitions. Here M is the number of terms
exact diagonalization, the only known exact solution to the             in the decomposition of the Hamiltonian and hmax is the
problem on a traditional computer. The QPU has been                     coefﬁcient with maximum norm in the decomposition of the
experimentally implemented using integrated photonics technol-          Hamiltonian. The advantage of this approach is that the
ogy with a spontaneous parametric downconversion single-                coherence time to make a single measurement after preparing
photon source and combined with an optimization algorithm               the state is O(1). Conversely, the disadvantage of this approach
run on a classical processing unit (CPU), which variationally           with respect to QPE is the scaling in the total number of
computes the eigenvalues and eigenvectors of H. By using a              operations, as a function of the desired precision is quadratically
variational algorithm, this approach reduces the requirement for        worse (O(p  2) versus O(p  1)). Moreover, this scaling will also
coherent evolution of the quantum state, making more efﬁcient           reﬂect the number of state preparation repetitions required,
use of quantum resources, and may offer an alternative route to         whereas in QPE the number of state preparation steps is
practical quantum-enhanced computation.                                 constant. In essence, we dramatically reduce the coherence time
                                                                        requirement while maintaining an exponential advantage over
Results                                                                 the classical case, by adding a polynomial number of repetitions
Quantum expectation estimation. The quantum expectation                 with respect to QPE.
estimation (QEE) algorithm computes the expectation value of a
given Hamiltonian H for an input state |cS. Any Hamiltonian
may be written as                                                       Quantum variational eigensolver. The procedure outlined above
                    X             X ij      j
                                                                        replaces the long coherent evolution required by QPE by many
               H¼       hia sia þ  hab sia sb þ . . .      ð1Þ          short coherent evolutions. In both QPE and QEE we require a
                       ia         ijab                                  good approximation to the ground-state wavefunction to com-
                                                                        pute the ground-state eigenvalue, and we now consider this
for real h, where Roman indices identify the subsystem on which         problem. Previous approaches have proposed to prepare ground
the operator acts, and Greek indices identify the Pauli operator,       states by adiabatic evolution15, or by the quantum Metropolis
for example, a ¼ x. Note that no assumption about the dimension         algorithm25,26. Unfortunately both of these require long coherent
or structure of the hermitian Hamiltonian is needed for this            evolution. The quantum variational eigensolver (QVE) algorithm
expansion to be valid. By exploiting the linearity of quantum           is a variational method to prepare the eigenstate and, by
observables, it follows that                                            exploiting QEE, requires short coherent evolution. QEE and
                      X                X ij
              hHi ¼       hia hsia i þ
                                                  j
                                        hab hsia sb i þ . . . ð2Þ       QVE and their relationship are shown in Fig. 1 and detailed in the
                      ia           ijab
                                                                        Supplementary Methods.
                                                                           It is well known that the eigenvalue problem for an observable
We consider Hamiltonians that can be written as a polynomial            represented by an operator H can be restated as a variational
number of terms, with respect to the system size. This class of         problem on the Rayleigh–Ritz quotient27,28, such that the
Hamiltonians encompasses a wide range of physical systems,              eigenvector |cS corresponding to the lowest eigenvalue is the

2                                                     NATURE COMMUNICATIONS | 5:4213 | DOI: 10.1038/ncomms5213 | www.nature.com/naturecommunications
                                          & 2014 Macmillan Publishers Limited. All rights reserved.

NATURE COMMUNICATIONS | DOI: 10.1038/ncomms5213                                                                                                                                                   ARTICLE

                                                                                                                         Quantum variational eigensolver
                                                                                                     Quantum expectation estimation
                                                                                                     QPU                                                                            CPU
                                                                                                              〈H1〉                          〈H1〉




                                                                                                                                                      Classical feedback decision
                                     Quantum state preparation
                                                                                  Quantum module 1                                           +
                                                                                                              〈H2〉                          〈H2〉




                                                                                                                          Classical adder
                                                                                  Quantum module 2
                                                                                                                                             +
                                                                                                              〈H3〉                          〈H3〉
                                                                                  Quantum module 3
                                                                                                                                             +
                                                                                                                                             +
                                                                                                              〈HN〉                          〈HN〉
                                                                                  Quantum module N




                                                                                Adjust the parameters for the next input state

Figure 1 | Architecture of the quantum-variational eigensolver. In QEE, quantum states that have been previously prepared are fed into the quantum
modules, which compute /HiS, where Hi is any given term in the sum deﬁning H. The results are passed to the CPU, which computes /HS. In the
quantum variational eigensolver, the classical minimization algorithm, run on the CPU, takes /HS and determines the new state parameters, which are
then fed back to the QPU.


|cS that minimizes                                                                                          written as
                                hc j H j ci                                                                                                                                          X
                                                                                                                                                                                     k
                                            :                                                        ð3Þ                                           T ðkÞ ¼                                 Ti :        ð8Þ
                                  hc j ci
                                                                                                                                                                                     i¼1
By varying the experimental parameters in the preparation of
                                                                                                            In general no efﬁcient implementation of this ansatz has yet been
|cS and computing the Rayleigh–Ritz quotient using QEE as
                                                                                                            developed for a classical computer, even for low-order cluster
a subroutine in a classical minimization, one may prepare
                                                                                                            operators, due to the non-truncation of the BCH series29.
unknown eigenvectors. At the termination of the algorithm, a
                                                                                                            However, this state may be prepared efﬁciently on a quantum
simple prescription for the reconstruction of the eigenvector is
                                                                                                            device. The reduced anti-hermitian cluster operator (T(k)  T(k)w)
stored in the ﬁnal set of experimental parameters that deﬁne |cS.
                                                                                                            is the sum of a polynomial number of terms—namely, it contains
   If a quantum state is characterized by an exponentially large
                                                                                                            a number of terms O(Nk(M  N)k), where M is the number of
number of parameters, it cannot be prepared with a polynomial
                                                                                                            single-particle orbitals. By deﬁning an effective Hermitian
number of operations. The set of efﬁciently preparable states are
                                                                                                            Hamiltonian H ¼ i(T(k)  T(k)w) and performing the Jordan–
therefore characterized by polynomially many parameters, and
                                                                                                            Wigner transformation to reach a Hamiltonian that acts on the
we choose a particular set of ansatz states of this type. Under                                                              ~ we are left with a Hamiltonian that is a sum of
                                                                                                            space of qubits, H,
these conditions, a classical search algorithm on the experimental
                                                                                                            polynomially many products of Pauli operators. The problem
parameters that deﬁne |cS needs only explore a polynomial
                                                                                                            then reduces to the quantum simulation of this effective
number of dimensions—a requirement for the search to be                                                                    ~ which can be done in polynomial time using
                                                                                                            Hamiltonian, H,
efﬁcient. One example of a quantum state parameterized by a
                                                                                                            the procedure outlined by Ortiz et al.23 We note that while this
polynomial number of parameters for which there is no known
                                                                                                            state preparation procedure utilizes tools from quantum
efﬁcient classical implementation is the unitary coupled cluster
                                                                                                            simulation, the total effective time of evolution is ﬁxed by the
ansatz29                                                                                                                              rs
                                                                                                            expansion coefﬁcients tpq    . This is in contrast to the normal
                                                                 w
                          j Ci ¼ eT  T j Firef :                                                    ð4Þ    difﬁculties encountered in QPE, where simulations must be
                                                                                                            carried out for times that are exponential in the desired bits of
where |FSref is some reference state, usually the Hartree Fock                                              precision.
ground state, and T is the cluster operator for an N electron                                                  While there is currently no known efﬁcient classical algorithm
system, deﬁned by                                                                                           based on these ansatz states, non-unitary coupled cluster ansatz is
                      T ¼ T1 þ T2 þ T3 þ ::: þ TN ;                                                  ð5Þ    sometimes referred to as the ‘gold standard of quantum
                                                                                                            chemistry’ as it is the standard of accuracy to which other
where                                                                                                       methods in quantum chemistry are often compared. The unitary
                                     X                                                                      version of this ansatz is thought to yield superior results to even
                              T1 ¼                               tpr ^awp ^ar                        ð6Þ
                                                                                                            this ‘gold standard’29.
                                                pr

                                  X                                                                         Prototype demonstration. We have implemented the QPU using
                                                       rs w w
                           T2 ¼                       tpq ^ap ^aq ^ar ^as                            ð7Þ
                                  pqrs
                                                                                                            integrated quantum photonics technology30. Our device, shown
                                                                                                            schematically in Fig. 2, is a reconﬁgurable waveguide chip that
and higher-order terms follow logically. It is clear that by                                                can prepare and measure arbitrary two-bit pure states using
construction the operator (T  Tw) is anti-hermitian,        T
                                                                                                            several single-qubit rotations and one two-qubit entangling gate.
and exponentiation maps it to a unitary operator U ¼ eðT  T Þ .                                            The state is path-encoded using photon pairs generated via a
For any ﬁxed excitation level k, the reduced cluster operator is                                            spontaneous parametric downconversion process. State

NATURE COMMUNICATIONS | 5:4213 | DOI: 10.1038/ncomms5213 | www.nature.com/naturecommunications                                                                                                          3
                                                                            & 2014 Macmillan Publishers Limited. All rights reserved.

ARTICLE                                                                                        NATURE COMMUNICATIONS | DOI: 10.1038/ncomms5213



    a
    |00〉                                                 〈|i ⊗ j |〉

                                                                                                        QPU                                    CPU
                                                            dc6                                                                      Optimization
                                                                                                                        D1            algorithm
                dc1           dc2                                                        dc9          dc10
                       1            2                                           5             6                     D2                〈H 〉
                                                            dc7
                                                                                                                        D3
                dc3           dc4          dc5                            dc11          dc12          dc13                               {ij}
                       3            4                                           7             8                     D4
                                                            dc8
                                                                                                                                         {ij}




    b
                                                         from CPU
                                                         From CPU




           From SPDC
           source
                                                                                               To detectors
                                                           QPU



                       1 cm

Figure 2 | Experimental implementation of our scheme. (a) Quantum-state preparation and measurement of the expectation values /c|si#sj|cS
are performed using a quantum photonic chip. Photon pairs, generated using spontaneous parametric downconversion, are injected into the waveguides
encoding the |00S state. The state |cS is prepared using thermal phase shifters f1  8 (orange rectangles) and one CNOT gate and measured using
photon detectors. dc{1–4,9–13} (dc5–7) are 50% (30%) reﬂectivity directional couplers. Coincidence count rates from the detectors D1–4 are passed
to the CPU running the optimization algorithm. This computes the set of parameters for the next state and writes them to the quantum device.
(b) A photograph of the QPU.


preparation and measurement in the Pauli basis is achieved by                    with the target state |cGS. The colour of each entry in Fig. 3a
setting 8 voltage-driven phase shifters and counting photon                      represents the tangle (absolute concurrence squared) of the state
detection events with silicon single-photon detectors31.                         at that step of the algorithm. It is known that the volume of
   The ability to prepare an arbitrary two-qubit separable or                    separable states is doubly exponentially small with respect to the
entangled state enables us to investigate 4  4 Hamiltonians. For                rest of state space33. Thus, the ability to traverse non-separable
the experimental demonstration of our algorithm we choose a                      state space increases the number of paths by which the algorithm
problem from quantum chemistry—namely, determining the                           can converge and will be a requirement for future large-scale
bond dissociation curve of the molecule He–H þ in a minimal                      implementations. Moreover, it is clear that the ability to produce
basis. The full conﬁguration interaction Hamiltonian for this                    entangled states is a necessity for the accurate description of
system has dimension 4, and can be written compactly as                          general quantum systems where eigenstates may be non-
                       X                X ij           j                         separable—for example, the ground state of the He–H þ
              HðRÞ ¼       hia ðRÞsia þ    hab ðRÞsia sb :    ð9Þ                Hamiltonian has small but not negligible tangle.
                         ia               ijab
                                                                                    Repeating this procedure for several values of R, we obtain the
                                  ij
The coefﬁcients    hia ðRÞ and   hab ðRÞ were determinedusing the                bond dissociation curve, which is reported in Fig. 4. After the
PSI3 computational package32 and are tabulated in                                computed energies have been corrected for experimental errors,
Supplementary Table 2.                                                           the determination of the equilibrium bond length of the molecule
   In order to compute the bond dissociation of the molecule, we                 was found to be R ¼ 92.3±0.1 pm, with a corresponding ground-
use QVE to compute its ground state for a range of values of the                 state electronic energy of E ¼  2.865±0.008 MJ mol  1. Full
nuclear separation R. In Fig. 3 we report a representative                       details of the correction for systematic errors and estimation of
optimization run for a particular nuclear separation, demonstrat-                the uncertainty on E are reported in the Supplementary Methods.
ing the convergence of our algorithm to the ground state of H(R)                 The corresponding theoretical curve shows the numerically exact
in the presence of experimental noise. Figure 3a demonstrates the                energy derived from a full conﬁguration interaction calculation of
convergence of the average energy, while Fig. 3b demonstrates the                the molecular system in the same basis. More than 96% of the
convergence of the overlap |/cj|cGS| of the current state |cjS                   experimental data are within chemical accuracy with respect to

4                                                            NATURE COMMUNICATIONS | 5:4213 | DOI: 10.1038/ncomms5213 | www.nature.com/naturecommunications
                                                 & 2014 Macmillan Publishers Limited. All rights reserved.

NATURE COMMUNICATIONS | DOI: 10.1038/ncomms5213                                                                                                                     ARTICLE

  a −0.5                                                                                                            20




                                                                                               Energy (MJ mol−1)
                                                                                 1                                                                           Theoretical 〈 〉
                                                                                                                    10                                       Experimental 〈 〉
                                                            Energy levels                                                                                    Corrected Exp. 〈 〉
                      −1                                    Theoretical 〈 〉
                                                                                                                     0
                                                            Experimental 〈 〉
 Energy (MJ mol−1)




                                                                      +
                     −1.5                                                                                          −10
                                                                  He




                                                                                     Tangle
                                                            H                                                             0        100             200            300             400
                                                                                                                                         Atomic separation R (pm)
                      −2                                                                                           −2.4


                     −2.5                                                                                          −2.5




                                                                                               Energy (MJ mol−1)
                      −3                                                         0                                 −2.6
                            0   20    40        60            80        100
                                     Optimization step j                                                           −2.7

  b                    1
                                                                                                                   −2.8
                      0.8
    State overlap




                      0.6                                                                                          −2.9

                      0.4                                                                                                     50   100       150        200       250      300
                      0.2                                                                                                                Atomic separation R (pm)

                       0                                                                      Figure 4 | Bond dissociation curve of the He–H þ molecule. This curve
                            0   20    40         60            80       100                   is obtained by repeated computation of the ground-state energy (as shown
                                     Optimization step j                                      in Fig. 3) for several H(R) values. The magniﬁed plot shows that after
                                                                                              correction for the measured systematic error the data overlap with the
Figure 3 | Finding the ground state of He–H þ for a speciﬁc molecular
                                                                                              theoretical energy curve, and, importantly, we can resolve the molecular
separation R ¼ 90 pm. (a) Experimentally computed energy /HS
                                                                                              separation of minimal energy. Error bars show the standard deviation of the
(coloured dots) as a function of the optimization step j. The colour
                                                                                              computed energy, as described in the Methods section.
represents the tangle (degree of entanglement) of the physical state,
estimated directly from the state parameters ffji g. The red lines indicate
the energy levels of H(R). The optimization algorithm clearly converges to                    QPE. In many cases (for example, our photonic implementation),
the ground state of the molecule, which has small but non-zero tangle. The                    repeated preparation of a state is not signiﬁcantly harder than
crosses show the energy calculated at each experimental step, assuming an                     preparation of a single copy, requiring only a polynomial
ideal quantum device. (b) Overlap |/cj|cGS between the experimentally                         overhead in time without any modiﬁcation of the device.
computed state |cjS at each optimization step j and the theoretical ground                       In implementing QVE, the device prepares ansatz states that
state of H, |cGS. Error bars are smaller than the data points. Further details                are deﬁned by a polynomial set of parameters. This ansatz might
are provided in the Methods section, Supplementary Table 1 and                                be chosen based on knowledge of the physical system of interest
Supplementary Methods.                                                                        (as for the unitary coupled cluster and typical quantum chemistry
                                                                                              ansätze), thus determining the device design. However, our
                                                                                              architecture allows for an alternative and potentially more
the theoretical values. At the conclusion of the optimization, we                             promising approach, where the device is ﬁrst constructed based
retain full knowledge of the experimental parameters, which can                               on the available resources and we deﬁne the set of states that the
be used for efﬁcient reconstruction of the state |cS in the event                             device can prepare as the ‘device ansatz’. Due to the quantum
that additional physical or chemical properties are required.                                 nature of the device, this ansatz can be very distinct from those
                                                                                              used in traditional quantum chemistry. With this alternative
                                                                                              approach the physical implementation is then given by a known
Discussion                                                                                    sequence of quantum operations with adjustable parameters—
QEE uses relatively few quantum resources compared to QPE.                                    determined at the construction of the device—with a maximum
Broadly speaking, QPE requires a large number of n-qubit                                      depth ﬁxed by the coherence time of the physical qubits. This
quantum controlled operations to be performed in series—                                      approach, while approximate, provides a variationally optimal
placing considerable demands on the number of components and                                  solution for the given quantum resources and may still be able to
coherence time—while the inherent parallelism of our scheme                                   provide qualitatively correct solutions, just as approximate
enables a small number of n-qubit gates to be exploited many                                  methods do in traditional quantum chemistry (for example,
times, drastically reducing these demands. Moreover, adding                                   Hartree Fock). The unitary coupled cluster ansatz (equation (4))
control to arbitrary unitary operations in practice is difﬁcult, if                           provides a concrete example where our approach provides an
not impossible, for current quantum architectures (although a                                 exponential advantage over known classical techniques. For this
proposed scheme to add control to arbitrary unitary operations                                ansatz, with as few as 40–50 qubits, one expects to manipulate a
has recently been demonstrated34). To give a numerical example,                               state that is not efﬁcient to simulate classically, and can provide a
the QPE circuit for a 4  4 Hamiltonian such as that                                          solution superior to the classical gold standard, non-unitary
demonstrated here would require at least 12 CNOT gates, while                                 coupled cluster.
our method only requires one. We note that the resource saving                                   We have developed and experimentally implemented a new
provided by QEE incurs a cost of polynomial repetitions of the                                approach to solving the eigenvalue problem with quantum
state preparation, as compared to the single copy required by                                 hardware. QEE shares with QPE the need to prepare a good

NATURE COMMUNICATIONS | 5:4213 | DOI: 10.1038/ncomms5213 | www.nature.com/naturecommunications                                                                                          5
                                                           & 2014 Macmillan Publishers Limited. All rights reserved.

ARTICLE                                                                                                NATURE COMMUNICATIONS | DOI: 10.1038/ncomms5213


approximation to the ground state, but replaces a single long                          described in the Methods. These phases are then applied to the CNOT-MZ chip
coherent evolution by a number of shorter coherent calculations                        using f1,2,3,4,7,8. Here f7,8 are modiﬁed to account for the choice of measurment
                                                                                       setting at the target qubit. (Any single-qubit projective measurement can be per-
proportional to the number of terms in the Hamiltonian. While                          formed using an MZI together with two phase shifters.) The measurement setting
the effect of errors on each of these calculations is the same as in                   for the control qubit is implemented using f5,6.
QPE, the reliance on a number of separate calculations makes the
algorithm sensitive to variations in state preparation between the
                                                                                       Estimation of the error on /HS. We performed measurements of the statistical
separate quantum calculations. This effect requires further                            and systematic errors that affect our computation of /HS.
investigation. The most general local Hamiltonian problem is
QMA-complete35. However, under the reasonable assumption
that a good approximation to the state can be prepared, our                            Statistical errors. Statistical errors due to the Poissonian noise associated with
                                                                                       single-photon statistics are intrinsic to the estimation of expectation values in
method and QPE can both efﬁciently estimate the energy of the                          quantum mechanics.
state, and it is in this setting that we compare them. In QVE, we                          These errors can be arbitrarily reduced at a sublinear cost of measurement time
experimentally implemented a ground-state preparation                                  (that is, efﬁciently) since the magnitude of error is proportional to the square root
procedure through a direct variational algorithm on the control                        of the count rate. We experimentally measured the standard deviation of an
                                                                                       expectation value /HiS for a particular state using 50 trials. The total average
parameters of the quantum hardware. The prepared state could                           coincidence rate was B1,500 s  1. The standard deviation was found to be 37 kJ
be utilized in either QEE 1 or QPE if desired. Larger calculations                     mol  1, which is comparable to the error observed in the measurement of the
will require a choice of ansatz, for which there are two                               ground-state energy shown in Fig. 4.
possibilities. One could experimentally implement chemically                               The minima of the potential energy curve was determined by a generalized least
                                                                                       squares procedure to ﬁt a quadratic curve to the experimental data points in the
motivated ansatz such as the unitary coupled cluster method.                           region R ¼ (80, 100) pm, as is common in the use of trust region searches for
Alternatively, one could pursue those ansätze that are most easy                      minima37, using the inverse experimentally measured variances as weights.
to implement experimentally—creating a new set of device ansatz                        Covariances determined by the generalized least squares procedure were used as
states that would require classiﬁcation in terms of their overlap                      input to a Monte Carlo sampling procedure to determine the minimum energy and
                                                                                       equilibrium bond distance as well as their uncertainties assuming Gaussian random
with chemical ground states. Such a classiﬁcation would be a good                      error. The uncertainties reported represent standard deviations. Sampling error in
way to determine the value of a given experimental advance—for                         the Monte Carlo procedure was 3  10  4 pm for the equilibrium bond distance
ground-state problems it is best to focus limited experimental                         and 3  10  8 MJ mol  1 for the energy.
resources on those efforts that will most enhance the overlap of                           In Fig. 4, the large deviations from the theoretical line result from the
preparable states with chemical ground states. In addition to the                      coincidental impact of noise resulting in premature optimization termination.
                                                                                       These points could have been rerun or eliminated using the prior knowledge of
above issues, which we leave to future work, an interesting avenue                     smoothness of the dissociation curve. However, to accurately portray the
of research is to ask whether the conceptual approach described                        performance of the algorithm exactly as described, with no expert interference,
here could be used to address other intractable problems with                          these points are retained.
quantum-enhanced computation. Examples that can be mapped
to the ground-state problem, and where the N-representability                          Systematic errors. In all the measurements described above we observed a con-
problem does not occur, include search engine optimization and                         stant and reproducible small shift, E ¼ 50 kJ mol  1, of the expectation value with
image recognition. It should be noted that the approach presented                      respect to the theoretical value of the energy. There are at least three effects that
here requires no control or auxiliary qubits, relying only on                          contribute to this systematic error.
                                                                                           Firstly, the downconversion source that we use in our experiment does not
measurement techniques that are already well established. For                          produce the pure two-photon state that is required for high-ﬁdelity quantum
example, in the two-qubit case, these measurements are identical                       interference. In particular, higher-order photon number terms and, more
to those performed in Bell inequality experiments.                                     signiﬁcantly, photon distinguishability both degrade the performance of our
   Quantum simulators with only a few tens of qubits are                               entangling gate and thus the preparation of the state |cS. This results in a shift of
                                                                                       the measured energy /c|H|cS. Higher-order terms could be effectively
expected to outperform the capabilities of conventional compu-                         eliminated by use of true single-photon sources (such as quantum dots or nitrogen
ters, not including open questions regarding fault tolerance and                       vacancy centers in diamond), and there is no fundamental limit to the degree of
errors/precision. Our scheme would allow such devices to be                            indistinguishability that can be achieved through improved state engineering.
implemented using dramatically less resources than the current                             Secondly, imperfections in the implementation of the photonic circuit also
                                                                                       reduce the ﬁdelity with which |cS is prepared and measured. Small deviations
best known approach.                                                                   from designed beamsplitter reﬂectivities and interferometer path lengths, as well as
                                                                                       imperfections in the calibration of voltage-controlled phase shifters used to
                                                                                       manipulate the state, all contribute to this effect. However, these are technological
Methods                                                                                limitations that can be greatly improved in future realizations.
Classical optimization algorithm. For the classical optimization step of our               Finally, unbalanced input and output coupling efﬁciency also results in skewed
integrated processor we implemented the Nelder–Mead (NM) algorithm36, a                two-photon statistics, again shifting the measured expectation value of /HS.
simplex-based direct search (DS) method for unconstrained minimization of                  Another systematic effect that can be noted in Fig. 4 is that the magnitude of the
objective functions. Although in general NM can fail because of the deterioration of   error on the experimental estimation of the ground-state energy increases with
the simplex geometry or lack of sufﬁcient decrease, the convergence of this method     R. This is due to the fact that as R increases the ﬁrst and second excited eigenstates
can be greatly improved by adopting a restarting strategy. Although other DS           of this Hamiltonian become degenerate, resulting in increased difﬁculty for the
methods, such as the gradient descent, can perform better for smooth functions,        classical minimization, generating mixtures of states that increases the overall
these are not robust to the noise, which makes the objective function non-smooth       variance of the estimation.
under experimental conditions. NM has the ability to explore neighbouring valleys
with better local optima, and likewise this exploring feature usually allows NM to
overcome non-smoothnesses. We veriﬁed that the gradient descent minimization           Quantum-state ﬁdelity. In a previous work31, we measured the average state
algorithm is not able to converge to the ground state of our Hamiltonian under the     ﬁdelity of states generated by the CNOT gate, estimated by quantum process
experimental conditions, mainly due to the Poissonian noise associated with our        tomography, to be 0.873±0.001. The average quantum-state ﬁdelity over four Bell
photon source and the accidental counts of the detection system, while NM              states was 0.93. The average ﬁdelity across 995 conﬁgurations (equivalent to many
converged to the global minimum in most optimization runs.                             truth tables in many bases) was 0.990±0.009, with 96% of conﬁgurations
                                                                                       producing photon statistics with f40.97.

Mapping from the state parameters to the chip phases. The set of phases {yi},
which uniquely identiﬁes the state |cS, is not equivalent to the phases that are       Count rate. In our experiment the mean count rate, which directly determines the
written to the photonic circuit {fi}, since the chip phases are also used to imple-    statistical error, was B2,000–4,000 twofold events per measurement. The expec-
ment the desired measurement operators sa#sb. Therefore, knowing the desired           tation value of a given Hamiltonian was reconstructed at each point from four two-
state parameters and measurement operator we compute the appropriate values of         qubit Pauli measurements. For the bond dissociation curve we measured about 100
the chip phases on the CPU at each iteration of the optimization algorithm. The        points per optimization run. In the full dissociation curve we found the ground
algorithm for ﬁnding the state parameters {yi} for an arbitrary two-qubit state is     states of 79 Hamiltonians. The full experiment was performed in about 158 h.

6                                                                  NATURE COMMUNICATIONS | 5:4213 | DOI: 10.1038/ncomms5213 | www.nature.com/naturecommunications
                                                     & 2014 Macmillan Publishers Limited. All rights reserved.

NATURE COMMUNICATIONS | DOI: 10.1038/ncomms5213                                                                                                                    ARTICLE

    State preparation is relatively fast, requiring a few milliseconds to set the phases   27. Rayleigh, J. W. In ﬁnding the correction for the open end of an organ-pipe.
on the chip. However, 17 s is required for cooling the chip, resulting in a duty cycle
                                                                                               Phil. Trans. 161, 77 (1870).
of B5%. The purpose of this is to overcome theinstability of the ﬁbre-to-chip
                                                                                           28. Ritz, W. Über eine neue Methode zur Lösung gewisser variationsprobleme der
coupling due to thermal expansion of the chip during operation. This will not be an
                                                                                               mathematischen physik. J. Reine Angew. Math. 135, 1–61 (1908).
issue in future implementations, where ﬁbres will be permanently ﬁxed to the
                                                                                           29. Taube, A. G. & Bartlett, R. J. New perspectives on unitary coupled-cluster
chip’s facets. Moreover, the thermal phase shifters used here will also likely be
                                                                                               theory. Int. J. Quant. Chem. 106, 3393–3401 (2006).
replaced by alternative technologies based on the electro-optic effect.
    Brighter single-photon sources will considerably reduce the measurement time.          30. O’Brien, J. L., Furusawa, A. & Vuckovic, J. Photonic quantum technologies.
                                                                                               Nat. Photon. 3, 687–695 (2009).
                                                                                           31. Shadbolt, P. et al. Generating, manipulating and measuring entanglement
References                                                                                     and mixture with a reconﬁgurable photonic circuit. Nat. Photon. 6, 45–49
1. Thogersen, L. & Olsen, J. A coupled cluster and full conﬁguration interaction               (2011).
    study of cn and cn-. Chem. Phys. Lett. 393, 36–43 (2004).                              32. Crawford, T. D. et al. Psi3: an open-source ab initio electronic structure
2. Helgaker, T., Jorgensen, P. & Olsen, J. Mol. Electronic Struct. Theory (Wiley,              package. J. Comp. Chem. 28, 1610–1616 (2007).
    Sussex, 2002).                                                                         33. Szarek, S. J. Volume of separable states is super-doubly-exponentially small in
3. Saad, Y. Numerical Methods for Large Eigenvalue Problems Vol. 158 (SIAM, 1992).             the number of qubits. Phys. Rev. A 72, 032304 (2005).
4. Page, L., Brin, S., Motwani, R. & Winograd, T. The Pagerank Citation Ranking:           34. Zhou, X.-Q. et al. Adding control to arbitrary unknown quantum operations.
    Bringing Order to the Web. Technical Report 1999-66 (Stanford InfoLab, 1999).              Nat. Commun. 2, 413 (2011).
5. Golub, G. H. & van der Vorst, H. A. Eigenvalue computation in the 20th                  35. Kempe, J., Kitaev, A. & Regev, O. The complexity of the local hamiltonian
    century. J. Comput. Appl. Math. 123, 35–65 (2000).                                         problem. SIAM J. Comput. 35, 1070–1097 (2006).
6. Nielsen, M. A. & Chuang, I. L. Quantum Computation and Quantum                          36. Nelder, J. A. & Mead, R. A simplex method for function minimization. Comput.
    Information (Cambridge University Press, 2000).                                            J. 7, 308–313 (1965).
7. Kitaev, A. Quantum measurements and the Abelian stabilizer problem.                     37. Conn, A. R., Gould, N. I. & Toint, P. L. Trust Region Methods Vol. 1 (Society for
    Electronic Colloquium on Computational Complexity (ECCC) 3 (1996).                         Industrial Mathematics, 1987).
8. Grifﬁths, R. B. & Niu, C.-S. Semiclassical fourier transform for quantum
    computation. Phys. Rev. Lett. 76, 3228–3231 (1996).
9. Neven, H., Rose, G. & Macready, W. G. Image recognition with an adiabatic               Acknowledgements
    quantum computer I. Mapping to quadratic unconstrained binary                          We thank Scott Aaronson, Robert Chapman, Seth Lloyd, Tim Ralph, Terry Rudolph,
    optimization. Preprint at http://arxiv.org/abs/0804.4457 (2008).                       Joe Fitzsimons and James Whitﬁeld for discussions. We acknowledge ﬁnancial support
                                                                                           from the UK EPSRC, ERC, QUANTIP, PHORBITECH, QESSENCE, Nokia, NSQI, the
10. Harrow, A., Hassidim, A. & Lloyd, S. Quantum algorithm for linear systems of
                                                                                           Templeton Foundation and the EU DIQIP. A.P. acknowledges a Royal Academy of
    equations. Phys. Rev. Lett. 103, 150502 (2009).
11. Berry, D. W. High-order quantum algorithm for solving linear differential              Engineering Research Fellowship and a ARC Discovery Early Career Researcher Award
    equations. J. Phys. A 47, 105301 (2014).                                               under project number DE140101700. J.M. is supported by the DOE Computational
                                                                                           Science Graduate Fellowship under grant number DE-FG02-97ER25308. M.-H.Y.
12. Garnerone, S., Zanardi, P. & Lidar, D. A. Adiabatic quantum algorithm for
                                                                                           acknowledges the support by the National Basic Research Program of China Grants
    search engine ranking. Phys. Rev. Lett. 108, 230506 (2012).
13. Abrams, D. S. & Lloyd, S. Simulation of many-body fermi systems on a                   2011CBA00300 and 2011CBA00301, the National Natural Science Foundation of China
    universal quantum computer. Phys. Rev. Lett. 79, 2586–2589 (1997).                     Grants 61033001 and 61361136003, and the Youth 1000-talent program. P.J.L. is
                                                                                           supported by NSF award PHY-0955518 and by AFOSR award no. FA9550-12-1-0046.
14. Abrams, D. S. & Lloyd, S. Quantum algorithm providing exponential
                                                                                           A.A.-G. acknowledges support from the NSF CCI award no. CHE-1037992, the Air Force
    speed increase for ﬁnding eigenvalues and eigenvectors. Phys. Rev. Lett. 83,
    5162–5165 (1999).                                                                      Ofﬁce of Scientiﬁc Research award no. FA9550-12-1-0046, the Camille and Henry
15. Aspuru-Guzik, A., Dutoi, A. D., Love, P. J. & Head-Gordon, M. Simulated                Dreyfus foundation and the Alfred P. Sloan Foundation. J.L.O’B. acknowledges a Royal
    quantum computation of molecular energies. Science 309, 1704–1707 (2005).              Society Wolfson Merit Award and a Royal Academy of Engineering Chair in Emerging
                                                                                           Technologies.
16. Lanyon, B. P. et al. Towards quantum chemistry on a quantum computer. Nat.
    Chem. 2, 106–111 (2010).
17. Whitﬁeld, J. D., Biamonte, J. & Aspuru-Guzik, A. Simulation of electronic structure    Author contributions
    hamiltonians using quantum computers. Mol. Phys. 109, 735–750 (2011).                  All authors contributed extensively to the work presented in this paper.
18. Aspuru-Guzik, A. & Walther, P. Photonic quantum simulators. Nat. Phys. 8,
    285–291 (2012).
19. Jones, N. C. et al. Faster quantum chemistry simulation on fault-tolerant              Additional information
    quantum computers. New J. Phys. 14, 115023 (2012).                                     Supplementary Information accompanies this paper at http://www.nature.com/
20. Lloyd, S. Computational capacity of the universe. Phys. Rev. Lett. 88, 237901          naturecommunications
    (2002).
                                                                                           Competing ﬁnancial interests: The authors declare no competing ﬁnancial interests.
21. Ma, X.-s., Dakic, B., Naylor, W., Zeilinger, A. & Walther, P. Quantum
    simulation of the wavefunction to probe frustrated Heisenberg spin systems.            Reprints and permission information is available online at http://npg.nature.com/
    Nat. Phys. 7, 399–405 (2011).                                                          reprintsandpermissions/
22. Oseledets, I. Approximation of 2d  2d matrices using tensor decomposition.
    SIAM J. Matrix Anal. A 31, 2130–2145 (2010).                                           How to cite this article: Peruzzo, A. et al. A variational eigenvalue solver on a photonic
23. Ortiz, G., Gubernatis, J. E., Knill, E. & Laﬂamme, R. Quantum algorithms for           quantum processor. Nat. Commun. 5:4213 doi: 10.1038/ncomms5213 (2014).
    fermionic simulations. Phys. Rev. A 64, 022319 (2001).
24. Liu, Y.-K., Christandl, M. & Verstraete, F. Quantum computational complexity                             This work is licensed under a Creative Commons Attribution-
    of the n-representability problem: Qma complete. Phys. Rev. Lett. 98, 110503                             NonCommercial-NoDerivs 4.0 International License. The images or
    (2007).                                                                                other third party material in this article are included in the article’s Creative Commons
25. Temme, K., Osborne, T. J., Vollbrecht, K. G., Poulin, D. & Verstraete, F.              license, unless indicated otherwise in the credit line; if the material is not included under
    Quantum Metropolis sampling. Nature 471, 87–90 (2011).                                 the Creative Commons license, users will need to obtain permission from the license
26. Yung, M.-H. & Aspuru-Guzik, A. A quantum-quantum Metropolis algorithm.                 holder to reproduce the material. To view a copy of this license, visit http://
    Proc. Natl Acad. Sci. USA 109, 754–759 (2012).                                         creativecommons.org/licenses/by-nc-nd/4.0/




NATURE COMMUNICATIONS | 5:4213 | DOI: 10.1038/ncomms5213 | www.nature.com/naturecommunications                                                                                        7
                                                        & 2014 Macmillan Publishers Limited. All rights reserved.
