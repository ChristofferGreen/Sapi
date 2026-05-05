# 05-compiler-aided-systematic-construction-of-large-scale-dna-strand-displacement-circuits

ARTICLE
Received 7 Aug 2016 | Accepted 21 Dec 2016 | Published 23 Feb 2017                            DOI: 10.1038/ncomms14373               OPEN

Compiler-aided systematic construction
of large-scale DNA strand displacement circuits
using unpuriﬁed components
Anupama J. Thubagere1, Chris Thachuk2, Joseph Berleant2, Robert F. Johnson1, Diana A. Ardelean3,
Kevin M. Cherry1 & Lulu Qian1,2



Biochemical circuits made of rationally designed DNA molecules are proofs of concept for
embedding control within complex molecular environments. They hold promise for trans-
forming the current technologies in chemistry, biology, medicine and material science by
introducing programmable and responsive behaviour to diverse molecular systems. As the
transformative power of a technology depends on its accessibility, two main challenges are an
automated design process and simple experimental procedures. Here we demonstrate the
use of circuit design software, combined with the use of unpuriﬁed strands and simpliﬁed
experimental procedures, for creating a complex DNA strand displacement circuit that
consists of 78 distinct species. We develop a systematic procedure for overcoming the
challenges involved in using unpuriﬁed DNA strands. We also develop a model that takes
synthesis errors into consideration and semi-quantitatively reproduces the experimental data.
Our methods now enable even novice researchers to successfully design and construct
complex DNA strand displacement circuits.




1 Bioengineering, California Institute of Technology, 1200 East California Boulevard, Pasadena, California 91125, USA. 2 Computer Science, California Institute of

Technology, 1200 East California Boulevard, Pasadena, California 91125, USA. 3 Applied and Computational Mathematics, California Institute of Technology, 1200
East California Boulevard, Pasadena, California 91125, USA. Correspondence and requests for materials should be addressed to L.Q. (email: luluqian@caltech.edu).

NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications                                                                1

ARTICLE                                                                             NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373




T
       he success of computer engineering has inspired attempts        describes a logic circuit with a list of input and output terminals,
       to use hierarchical and systematic approaches for devel-        and a list of AND, OR, NOT, NAND and NOR gates with the
       oping molecular devices with increasing complexity. To          connectivity of their terminals speciﬁed. First, a technique called
enable the design and construction of a wide range of functional       dual-rail logic is applied to translate the original logic circuit into
molecular systems, we need software tools such as a compiler that      an equivalent circuit that contains AND and OR gates only25.
can automatically translate high-level functions to low-level          This is because the NOT gate cannot be directly implemented in
molecular implementations and provide models and simulations           multi-layer use-once DNA circuits, if the OFF and ON state of a
for predicting and debugging the behaviours of designed                signal is represented by low and high concentration of a single
molecular systems. The mechanism of DNA strand displacement            DNA strand, respectively. If a NOT gate were implemented this
has been used to create a variety of synthetic molecular systems       way, then output molecules of the gate could be immediately
including circuits, motors and triggered assembly of structures1.      produced in the absence of input. However, once this reaction
Software tools have been developed for designing and analysing         reaches equilibrium it cannot be reversed, even if input mole-
DNA strand displacement systems, capable of generating nucleic         cules are added at a later point. With dual-rail logic, each terminal
acid sequences from well-deﬁned structures and molecular               in the original circuit is replaced by two terminals, representing
interactions2,3, calculating the thermodynamic2,4,5 and kinetic6       the OFF and ON states of a signal separately (for example,
properties of designed molecules, and evaluating if the behaviours     each input signal xi is replaced by xi0 and xi1 ). Thus, no reaction
of the molecular systems agree with the higher-level designs3,7–11.    will take place until signal molecules on one of the two wires
There also exist a few molecular compilers that can translate          have arrived. With this representation, the NOT gate
abstract functions such as a logic function to DNA strand              can be implemented by exchanging the two wires of an
displacement implementations without requiring an under-               input and output signal. Each AND, OR, NAND and NOR
standing of the molecular level details12,13. However, there           gate in the original circuit is replaced by a pair of AND and OR
has been little independent experimental validation of these           gates.
compilers, most of which were developed in parallel with or after         Next, the compiler translates the dual-rail logic circuit into an
experimental ﬁndings12,14.                                             equivalent seesaw DNA circuit. In a seesaw DNA circuit, each
   In addition to software tools that facilitate automated design      signal is deﬁned as a wire wj,i connecting seesaw nodes j and i,
and analysis of DNA strand displacement circuits, we also need to      and implemented using a single-stranded DNA molecule.
simplify the experimental procedures for creating these circuits       Each AND and OR gate in the dual-rail circuit is replaced by a
in vitro, so that it is possible for researchers with diverse          seesaw AND and OR gate, respectively, which is deﬁned as a
backgrounds to build their own circuits and explore potential          pair of integrating and amplifying seesaw nodes connected with a
applications. A great inspiration is DNA origami15, a technique        set of input and output wires12. The seesaw nodes are
that folds DNA into sophisticated structures. In just 10 years         composed of double-stranded threshold and gate:output
since its birth, DNA origami has become one of the most                molecules and single-stranded fuel molecules (Fig. 1, bottom
signiﬁcant successes in the ﬁeld of DNA nanotechnology.                right). We will explain how the seesaw logic gates work in the
Over 170 research groups have contributed to advancing this            next section. Input fan-out gates are introduced to take an input
technique or developing it for applications in a variety of            signal that is used for multiple logic gates and produce the
research areas16–19. A fundamental reason why DNA origami              corresponding number of output signals. Reporters are
was able to quickly spread around the world is that the                introduced to take each output signal and generate a distinct
experimental procedure is extremely simple and makes use of            ﬂuorescence signal for readout.
cheap, unpuriﬁed nucleic-acid strands. In contrast, other                 Finally, the compiler generates Visual DSD3,26 code and
than a few very simple circuits with just one or two double-           Mathematica code for simulating and analysing the seesaw DNA
stranded components20, most DNA strand displacement circuits           circuit and a ﬁle that contains DNA sequences for all molecular
were constructed using strands that were purchased either              species in the circuit. The Visual DSD code can be used to
puriﬁed or unpuriﬁed, but all followed by in-house                     automatically produce diagrams of species, reactions and network
polyacrylamide gel electrophoresis (PAGE) puriﬁcation to               graphs with domain-level representation of DNA and to simulate
reduce undesired products due to synthesis errors and                  the circuit behaviour based on the network of chemical reactions.
stoichiometry errors12,14,21. Puriﬁed strands are approximately        The Mathematica code provides more customized and efﬁcient
ten times more expensive than unpuriﬁed strands, which                 simulations of seesaw circuits. The simulation uses the
signiﬁcantly increases the cost for building large-scale DNA           CRNSimulator package27 and models a speciﬁc set of side
circuits. In-house PAGE puriﬁcation is both time consuming and         reactions in addition to the designed reactions in a seesaw
labour intensive.                                                      network12.
   In this work, we show that one can successfully build                  As a demonstration of using the Seesaw Compiler, we
a complex DNA strand displacement circuit, using DNA                   designed a single DNA strand displacement circuit that
sequences automatically generated from a molecular compiler.           implements two distinct elementary cellular automata
We also show that one can even do so using cheap, unpuriﬁed            transition functions. An elementary cellular automaton (CA) is
DNA strands, following simple and systematic experimental              one of the simplest models of computation28. It consists of a
procedures.                                                            one-dimensional grid of cells, collectively called a generation,
                                                                       where each cell has a binary state of 0 or 1. In each subsequent
                                                                       generation, the state for a cell C is determined by its current
Results                                                                state and those of its left neighbour L and right neighbour
Circuit design. A simple DNA strand displacement motif called          R. A state transition rule maps each of the 23 ¼ 8 possible
the seesaw gate was developed to scale up the complexity of            combinations of states for L, C and R to either 0 or 1.
DNA circuits22 and was used to demonstrate digital logic               Thus, a length 8 binary string uniquely identiﬁes one of the 28
computation12 and neural network computation23. The Seesaw             possible transition functions that specify how an elementary
Compiler12,24 was developed to automatically translate an              CA will evolve between generations. The rule 110 elementary CA
arbitrary feed forward digital logic circuit into its equivalent       (binary number 01101110 written in decimal) is famously known
seesaw DNA circuit (Fig. 1). The compiler takes an input ﬁle that      to be Turing universal29.

2                                                  NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications

NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373                                                                                                                                                       ARTICLE

   Feedforward logic circuit                                               Visual DSD code                                                       Visual DSD simulation
   INPUT(1)              # x1
   INPUT(2)              # x2               directive plot <_ _ _ Fluor52> (* y1^0 *)                                                                                       S41L S41                S41R
   INPUT(3)              # x3               directive plot <_ _ _ Fluor54> (* y1^1 *)
                                                                                                                                                      S40R*          T* S41L*            S41*     S41R*
   INPUT(4)              # x4
                                                                                                                                                                                +
                                            def normal = 0.0003 (* normal toehold binding rate constant nM^-1 s^-1*)
                                                                                                                                              S40L        S40        S40R        T       S41L       S41     S41R
   OUTPUT(11)            # y1               def slow = 0.000015 (* slow toehold binding rate constant nM^-1 s^-1*)
   OUTPUT(8)             # y2                                                                                                                                                    ↓
                                            (* a seesaw signal *)                                                                             S40L        S40        S40R       T     S41L        S41       S41R

   5 = NOR(1, 2)                            def signal(N,iL,i,iR,jL,j,jR) = ( N * <iL^ iiR^ T^ jL^ j jR^>)
                                                                                                                                                                 S40R*          T* S41L* S41*               S41R*
   6 = NOT(4)                                                                                                                                                                   +
   7 = AND(3, 6)                            (* 2-input 2-output seesaw OR gate *)
                                                                                                                                                                 S41L           S41        S41R
   8 = OR(3, 4)                             def seesawOR2I2O(i1L,i1,i1R,i2L,i2,i2R,k1L,k1,k1R,k2L,k2,k2R)=
   9 = NAND(5, 3, 4)                        (gateL(20*N,i1L,i1,i1R,i2L,i2,i2R)
                                                                                                                                                S41L           S41     S41R          T     S42L      S42     S42R
   10 = OR(5, 7)                            | thresholdL(6*N,i1R,i2L,i2,i2R)
   11 = NAND(9, 10)                         | gateL(10*N,i2L,i2,i2R,k1L,k1,k1R)                                                               T* S41L*         S41* S41R*             T*
                                            | gateL(10*N,i2L,i2,i2R,k2L,k2,k2R)                                                                                                 +
                                            | signal(40*N,i2L,i2,i2R,fL,f,fR))                                                                 S40L        S40       S40R        T       S41L       S41     S41R


                                            ( signal(ON,S5L,S5,S5R,S22L,S22,S22R) (* x1^0 *)
                                                                                                                                          S40L        S40        S40R T              S41L       S41        S41R
                                            | signal(OFF,S7L,S7,S7R,S20L,S20,S20R) (* x1^1 *)
                                                                                                                                                                            T* S41L*            S41* S41R* T*
      Dual-rail logic circuit               | seesawOR2I2O(S20L,S20,S20R,S21L,S21,S21R,S38L,S38,S38R,S40L,S40,S40R)                                                             +
                                            | seesawAND2I2O(S22L,S22,S22R,S23L,S23,S23R,S36L,S36,S36R,S42L,S42,S42R)                          S41L        S41        S41R        T       S42L       S42     S42R

   INPUT(2)              # x1^0
   INPUT(3)              # x1^1

   OUTPUT(22)            # y1^0                                                                                                                 Mathematica simulation
                                                                          Mathematica code
   OUTPUT(23)            # y1^1

   10 = OR(3, 5)                            (* Rate constants: *)
   11 = AND(2, 4)                                                                                                                                                x4 x3 x2 x1 = 1001
                                            kf = 2*10^6; (* fast strand displacement rate, unit: M^–1 s^ –1 *)
   14 = OR(6, 9)                            ks = 5*10^4; (* slow strand displacement rate, unit: M^ –1 s^–1 *)                      1.0
   15 = AND(7, 8)
   16 = AND(6, 8)                           (* Translates a seesaw gate into a list of reactions: *)                                0.8
   17 = OR(7, 9)                                                                                                                                                                                                         y20
                                            seesaw[x_,l_List,r_List]:={
   18 = AND(11, 7, 9)                       (* Toehold exchange reactions *)                                                        0.6                                                                                  y21




                                                                                                                           Output
   19 = OR(10, 6, 8)                        Outer[revrxn[w[#1,x]+g[x,w[x,#2]],g[w[#1,x],x]+w[x,#2],ks,ks]&,l,r],
                                                                                                                                    0.4                                                                                  y10
                                            (* Translates logic OR operation into a list of seesaw gates *)
                                                                                                                                                                                                                         y11
                                            seesawOR[x1_,x2_,l_List,r_List]:=Module[{f},                                            0.2
                                            {seesaw[x1,l,{x2}],
                                                                                                                                    0.0
                                            (* Simulation *)                                                                              0            2               4       6                       8           10
                                            SIMcircuit=Table[gatesys={                                                                                                Time (hours)
      Seesaw DNA circuit                    seesawOR[20,21,{7,11},{38,40}],
                                            seesawAND[22,23,{5,9},{36,42}],
   INPUT(2) = w[5,22]        # x1^0
   INPUT(3) = w[7,20]        # x1^1         (* Plot *)                                                                                                Gate:Output (G5:5,6)
                                            Plot[Evaluate[SIMcircuit],{t,0,time},                                                                                                                      S6
   OUTPUT(22) = Fluor[52] # y1^0
   OUTPUT(23) = Fluor[54] # y1^1
                                                                                                                                                                          S5                    T

   inputfanout[13,12,{28,32,38}]
   inputfanout[15,14,{30,34,36}]                                              DNA sequences                                                               T*              S5*                   T*


   seesawOR[20,21,{7,11},{38,40}]           S5 =                                  S5* =                                              Input (w53,5)                                                   Reporter (Rep6)
   seesawAND[22,23,{5,9},{36,42}]           S7 =                                  S7* =
                                            S9 =                                  S9* =                                        S53
   seesawOR[28,29,{13,19},{40}]                                                                                                                                                                                   S6
                                                                                                                                                                                                                               Q
   seesawAND[30,31,{15,17},{42}]                                                                                                                                                                                               F
                                            x1^0: w5,22 = S22 T S5
                                                                                                                                      T               S5
                                                                                                                                                                                                  T*              S6*
   Reporter[52,45]                          x1^1: w7,20 = S20 T S7
                                                                                                                                                                      5                                6
   Reporter[54,47]
                                            Th12,13:13-t    = S13
                                                                                                                                                      1
                                            Th12,13:13-b     = s12* T* S13*                                                               53                   –0.5         1                   –1.5
                                            w13,28         = S28 T S13                                                                                                                2
                                            w13,32         = S32 T S13
                                                                                                                                                                                           f
                                            G13-b          = T* S13* T*
                                            w13,f          = Sf T S13                                                        Threshold (Th53,5:5)                                         Fuel (w5,f)
                                                                                                                                                                                                                        Sf
                                            Rep48-t        = RQ S48                                                                                       S5
                                            Rep48-b        = T* S48* ATTO590                                                                                                                                        T
                                                                                                                                                                                                    S5
                                                                                                                           s53* T*                        S5*


Figure 1 | Automated circuit design steps using the Seesaw Compiler. A feedforward digital logic circuit is ﬁrst translated into an equivalent dual-rail logic
circuit and then translated into an equivalent seesaw DNA circuit. Visual DSD code and Mathematica code are generated for analysing and simulating the
seesaw DNA circuit, and DNA sequences are generated for constructing the circuit. Bottom right diagram introduces the notations of seesaw circuits: black
numbers indicate identities of nodes. The locations and values of red numbers indicate the identities of distinct DNA species and their relative initial
concentrations, respectively.



   Another rule that is equally powerful is rule 124 (binary                                     circuit to demonstrate an interesting logic function associated
number 01111100 written in decimal), generated by applying the                                   with cellular automata and not to implement the actual cellular
following mirror transformation: the new state of the centre cell                                automata model. The circuit operates in a well-mixed test tube
for LCR ¼ zyx in rule 124 is the same as the new state for                                       environment that does not involve spatial dynamics (that is, no
LCR ¼ xyz in rule 110. Our circuit was designed to compute a                                     geometry of cells).
combined logic function of the two transition rules (Fig. 2a). It                                   The DNA circuit generated by the Seesaw Compiler consisted
consists of ﬁve logic gates in two layers, including a three-input                               of 6 layers and a total of 78 distinct initial DNA species (Fig. 2b
two-output NAND gate. It is noteworthy that we designed the                                      and Supplementary Fig. 1). Mathematica simulations of the DNA

NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications                                                                                                                                   3

ARTICLE                                                                                                                                        NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373



            a                                                                     b
                L                                                                 L0

                                                              R124
              C                                                                                                                                                                                      R1240
                                                              R110                L1
              R
                                                                                                                                                                                                     R1241
                           Rule 110                Rule 124
                                                                                  C0

                       LCR             R124          R110
                       000               0                0
                       001               0                1                       C1
                                                                                                                                                                                                     R1100
                       010               1                1
                       011               1                1
                                                                                                                                                                                                     R1101
                       100               1                0                       R0
                       101               1                1
                       110               1                1
                                                                                  R1
                       111               0                0



            c                      LCR = 000                                          LCR = 001                                     LCR = 010                                   LCR = 011
                     1.0                                                1.0                                         1.0                                           1.0
                     0.8                                                0.8                                         0.8                                           0.8
            Output




                                                               Output




                                                                                                                                                         Output
                     0.6                                                0.6                                Output   0.6                                           0.6
                     0.4                                                0.4                                         0.4                                           0.4
                     0.2                                                0.2                                         0.2                                           0.2
                     0.0                                                0.0                                         0.0                                           0.0                                R1240
                           0   2     4    6    8     10                       0   2     4    6    8   10                  0     2     4   6   8     10                  0   2    4    6     8   10
                                                                                                                                                                                                     R1241
                                    Time (h)                                           Time (h)                                      Time (h)                                   Time (h)
                                   LCR = 100                                          LCR = 101                                     LCR = 110                                   LCR = 111            R1100
                     1.0                                                1.0                                         1.0                                           1.0
                                                                                                                                                                                                     R1101
                     0.8                                                0.8                                         0.8                                           0.8
                                                                                                           Output
            Output




                                                               Output




                                                                                                                                                         Output
                     0.6                                                0.6                                         0.6                                           0.6
                     0.4                                                0.4                                         0.4                                           0.4
                     0.2                                                0.2                                         0.2                                           0.2
                     0.0                                                0.0                                         0.0                                           0.0
                           0   2     4    6    8     10                       0   2     4   6     8   10                  0     2    4    6     8   10                  0   2    4    6     8   10
                                    Time (h)                                           Time (h)                                     Time (h)                                    Time (h)

Figure 2 | Design of a rule 110–124 circuit using the Seesaw Compiler. (a) Gate diagram and truth table of a digital logic circuit that computes the
transition rules 110 and 124 of elementary cellular automata. (b) Seesaw gate diagram of the equivalent DNA strand displacement circuit. Each seesaw
node connected to a dual-rail input implements input fan-out. Each pair of seesaw nodes labelled 4 and 3 implements a dual-rail AND and OR gate,
respectively. Each pair of dual-rail AND and OR gates implements an AND, OR or NAND gate in the original logic circuit. Each dual-rail output is converted
to a ﬂuorescence signal through a reporter, indicated as a half node with a zigzag arrow. Each circle and dot inside a seesaw node indicates a double-
stranded threshold and gate molecule, respectively. Each dot on a wire indicates a single-stranded fuel molecule. (c) Simulations of the DNA strand
displacement circuit using the previously developed model for puriﬁed seesaw circuits. Trajectories and their corresponding outputs have matching colours.
Overlapping trajectories were shifted to be visible. Dotted and solid lines indicate dual-rail outputs that represent logic OFF and ON, respectively. For
example, when input LCR ¼ 001, meaning L0, C0 and R1 were introduced at a high concentration and L1, C1 and R0 at a low concentration, two output
trajectories R1240 and R1101 reached an ON state and the other two output trajectories R1241 and R1100 remained in an OFF state, indicating that the output
was computed to be 0 and 1 for rule 124 and 110, respectively. Simulations were performed at 1  ¼ 50 nM—the compiler recommended standard
concentration for large-scale puriﬁed seesaw circuits.



circuit predicted correct computation for all 8 possible input                                                                compensating for the signal decay that occurs during circuit
combinations under ideal experimental conditions (Fig. 2c).                                                                   execution. In seesaw circuits, digital signal restoration is a
   The next step was to construct the DNA circuit using                                                                       component of every logic gate, and is implemented by an
strands that were purchased unpuriﬁed and with no additional                                                                  amplifying seesaw node with the following idealized input-output
in-house puriﬁcation. We expected that the main challenges                                                                    function:
would be to understand how synthesis errors and stoichiometry                                                                                             
                                                                                                                                                            1 x4th
errors affect the behaviours of DNA circuits and to                                                                                                    y¼                                  ð1Þ
                                                                                                                                                            0 x  th
explore solutions that restore the desired circuit behaviour.
We took a bottom-up approach and began building the DNA                                                                       At the molecular level, the digital signal restoration process
circuit from the simplest functional component—digital signal                                                                 consists of two basic reactions: catalysis and thresholding.
restoration.                                                                                                                  Catalysis is implemented with two toehold exchange pathways
                                                                                                                              that release free output strands wi,k from double-stranded gate
                                                                                                                              molecules Gi:i,k, using the input strands wj,i as a catalyst (Supple-
Calibrating effective concentrations. Digital signal restoration is                                                           mentary Fig. 2a):
a process that pushes the intrinsically analog signal towards either
the ideal ON or OFF state, therefore cleaning up the noise and                                                                                                    wj;i þ Gi:i;k k!w
                                                                                                                                                                                  s
                                                                                                                                                                                    j;i þ wi;k               ð2Þ

4                                                                                          NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications

NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373                                                                                                                                                                                               ARTICLE

Catalysis can be used for signal ampliﬁcation, since a small                                                                                            species:
amount of input can trigger the release of a much larger amount                                                                                                                                                
                                                                                                                                                                                                               
                                                                                                                                                                                                          wj;i eff
of output.                                                                                                                                                                                         aj;i ¼                                                          ð4Þ
   Thresholding is implemented with double-stranded threshold                                                                                                                                            wj;i nom
molecules Thj,i:i consuming the input at a much faster rate                                                                                                                                                     
(kfcks) than the input acting as a catalyst (Supplementary                                                                                                                                               Thj;i:i eff
                                                                                                                                                                                               bj;i ¼                                                              ð5Þ
Fig. 2b):                                                                                                                                                                                               Thj;i:i nom
                                                                                                                                                                                                               
                                                              wj;i þ Thj;i:i k!+
                                                                               f
                                                                                                                                      ð3Þ                                                                 Gi:i;k eff
                                                                                                                                                                                               gi;k ¼                                                              ð6Þ
                                                                                                                                                                                                        Gi:i;k nom
   As shown in simulations generated using the Seesaw                                                                                                      The effective to nominal concentration of a DNA species
Compiler (Fig. 3a), when the concentration of the                                                                                                       cannot be measured in isolation. More importantly, the absolute
threshold molecule is 0.5  (where 1  is a standard                                                                                                    values of a, b and g should only affect the speed but not the
concentration of 100 nM), we expect that input less                                                                                                     correctness of computation, if the values remain comparable to
than the threshold (for example, 0.3  ) should be cleaned                                                                                              each other. Thus, we chose to estimate the ratio between b and a
up to an ideal OFF state via reaction 3 and input greater                                                                                               for a threshold consuming a signal, by comparing simulation
than the threshold (for example, 0.7  ) should be ampliﬁed                                                                                             with experimental result of a signal restoration circuit. For
to an ideal ON state via reaction 2. However, the                                                                                                       example, manipulating
                                                                                                                                                                                    the threshold value in simulation (sim)
observed circuit behaviour was different: when input ¼ 0.7  ,                                                                                          identiﬁed that Th53;5:5 sim ¼0:7 agreed with the experimental
the output signal was higher than an ideal OFF state, but                                                                                               data (Fig. 3c), which means the effective concentration                        of the
did not reach an ideal ON state (Fig. 3b). This experimental                                                                                            threshold
                                                                                                                                                                  was
                                                                                                                                                                       similar    to  that    of    the  signal    for   Th 53;5:5  nom
                                                                                                                                                                                                                                         ¼0:5
result suggested that the input did not sufﬁciently exceed                                                                                              and w53;5 nom ¼0:7. Thus, the threshold to signal ratio can be
the threshold, which was an indication that the effective                                                                                               calculated as:
concentration of an unpuriﬁed threshold species, compared                                                                                                                                        
with that of an unpuriﬁed signal species, was higher than                                                                                                  b53;5      Th53;5:5 eff        w53;5 nom
                                                                                                                                                                 ¼                               
expected.                                                                                                                                                  a53;5     Th53;5:5 nom          w53;5 eff
   The nominal concentration of a DNA species can be                                                                                                                              
measured using ultraviolet absorbance, but it can be higher                                                                                                            w53;5 nom                                   0:7
                                                                                                                                                                 ¼                                             ¼      ¼1:4               ð7Þ
than the effective concentration, which is the concentration of                                                                                                      Th53;5:5 nom                                   0:5
                                                                                                                                                                                      ½Th53;5:5 eff ¼½w53;5 eff
the DNA species actually performing the desired reactions. If
the sequences of the DNA strands are properly designed, the                                                                                               A possible explanation for an unpuriﬁed threshold having a
difference between nominal concentration and effective con-                                                                                             higher effective concentration than an unpuriﬁed signal, when the
centration is typically caused by synthesis errors including                                                                                            nominal concentrations are the same, is the following: the
nucleotide insertion, deletion and mismatch. To calibrate the                                                                                           synthesis errors of an unpuriﬁed strand depend on the length of
effective concentrations of unpuriﬁed DNA molecules, we                                                                                                 the strand, because in the process of chemical synthesis each
deﬁned the following ratio between effective (eff) and nominal                                                                                          nucleotide is attached to a growing chain of oligonucleotide
(nom) concentrations of an arbitrary signal, threshold and gate                                                                                         one at a time and the coupling efﬁciency of each step is less than



 a                                                                                                                                   b                                                                c
                                                                   1.0                                                                        1.0                                                              1.0
                                                                   0.8                                                                        0.8                                                              0.8
                                                                               [Th53,5:5]sim = 0.5 ×                Input                                  [Th53,5:5]nom = 0.5 ×           Input                         [Th53,5:5]sim = 0.7 ×                    Input
                                                          Output




                                                                                                                                     Output




                                                                                                                                                                                                      Output




      Input       5                   6                            0.6                                                                        0.6                                                              0.6
      W53,5                                                                                                         0                                                                      0                             [Th53,5:5]nom = 0.5 ×                    0
 53            –0.5   1            –1.5           y                0.4                                              0.3                       0.4                                          0.3                 0.4                                                0.3
                           2
                                                                   0.2                                              0.7                       0.2                                          0.7                 0.2                                                0.7
                               f                                                                                    1                                                                      1                                                                      1
                                                                   0.0                                                                        0.0                                                              0.0
                                                                         0        2      4    6      8        10                                    0       2    4    6       8       10                             0   2        4    6              8   10
                                                                                        Time (h)                                                                Time (h)                                                         Time (h)

 d                                                                                                                                                                                                    e
          x1          10                  1                        23                                                                                                                                          1.0
     21                                                                               1.0                                                     1.0
                           2        –0.6      1               –1.5       y            0.8                                                     0.8                                                              0.8
                                                      2                                                                                                                                    x1 x2                         [G1:1,23]tri = 0.8 ×                     x1x2
                                                                             Output




                                                                                                                                     Output




                                                                                                                                                                                                      Output




     27                                                   f                           0.6                                                     0.6                                                              0.6
          x2    [Th10,1:1]nom = 0.35 ×                                                                   x1                                                        x1                      0 0
                                                                                                         x2        OR       y                                      x2   AND       y        0 1                                    1              23                00
                                                                                      0.4                                                     0.4                                                              0.4
          x1          53                  5                        6                                                                                                                       1 0                           x1               x2                       20
     18                                                                                                                                                                                                                                                   y
                                                                                      0.2                                                     0.2                                          1 1                 0.2 10                 1        –1.5                01
                           2        –1.2      1               –1.5       y
                                                      2                               0.0                                                     0.0                                                              0.0
     22                                                   f
          x2                                                                                0   2    4    6             8       10                  0      2     4    6       8       10                             0       2      4     6                   8
                [Th53,5:5]nom = 0.85 ×
                                                                                                    Time (h)                                                    Time (h)                                                         Time (h)

Figure 3 | Calibrating effective concentrations. (a) Simulations and (b) experimental data of digital signal restoration. (c) Estimating effective threshold
concentration by ﬁtting simulations to the data obtained. (d) OR and AND logic gates constructed using adjusted nominal threshold concentrations.
(e) Estimating effective gate concentration. Data show steady-state ﬂuorescence level. 1  ¼ 100 nM. Here and in later ﬁgures, all output signals in the
data were normalized using the minimum ﬂuorescence signal (the ﬁrst data point) of an OFF trajectory as 0 and the maximum ﬂuorescence signal
(the average of the last ﬁve data points) of an ON trajectory as 1.

NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications                                                                                                                                                                          5

ARTICLE                                                                                       NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373


100% (ref. 30). Threshold molecules are composed of shorter                      (Supplementary Fig. 5). We suspect that due to synthesis errors in
strands (15 and 25 nucleotides) than signal molecules                            gate molecules, not all gates can successfully release a signal,
(33 nucleotides) and thus may contain fewer synthesis errors.                    which is why an unpuriﬁed gate has a lower effective concen-
   Additional signal restoration experiments suggested that the                  tration compared to a signal.
threshold to signal ratio b/a ¼ 1.4 was consistent for different                    As signal restoration was built in within every logic gate to
threshold and signal molecules (Supplementary Fig. 3). Thus,                     accept an ON state of [0.8, 1], we decided not to make any
using this ratio, we can then calculate how to adjust the nominal                adjustment for nominal gate concentrations if g/aZ0.8. Other-
thresholds for correctly computing logic AND and OR.                             wise, nominal concentration of an amplifying gate and an n-input
   Each seesaw logic gate has an integrating node upstream of an                 integrating gate can be adjusted as:
amplifying node. Ideally, an integrating node outputs the sum of                                                          a
all inputs:                                                                                               ½GAMP nom ¼1                      ð15Þ
                                                                                                                          g
                                  Xn
                              y¼      xi                      ð8Þ                                                               a
                                                                                                               ½GINT nom ¼n                           ð16Þ
                                       i¼1                                                                                      g
A two-input logic function can be computed as:                                      Importantly, the values of a, b and g should depend on the
                          
                            1 x1 þ x2 4th                                        strand quality and thus could vary with different DNA synthesis
                      y¼                                                  ð9Þ    providers, procedures and even batches. It is necessary to
                            0 x1 þ x2  th
                                                                                 recalculate the ratios b/a and g/a, if these conditions change.
Assuming that an ideal OFF state is [0, 0.2] and an ideal ON state
is [0.8, 1], th ¼ 0.6 will compute logic OR and th ¼ 1.2 will
                                                                                 Identifying outliers. With calibrated logic gates, we investigated
compute logic AND, if the effective concentrations of the
                                                                                 how well they compose together in larger circuits. We constructed
threshold and input signals are comparable to each other (that
                                                                                 a two-layer logic circuit that is part of the rule 124 sub-circuit and
is, b/a ¼ 1).
                                                                                 is composed of an AND gate and two upstream OR gates
   As b/aa1 for unpuriﬁed threshold and signal molecules, we
                                                                                 (Fig. 4a). The expected circuit behaviour is that the output should
can take this ratio into consideration while calculating the lower
                                                                                 remain OFF when only one of the upstream OR gates is ON.
and upper bounds of the nominal threshold for an n-input logic
                                                                                 However, the observed circuit behaviour showed that the output
gate:
                                                                                 was reasonably OFF when one upstream OR gate was ON, but
                          a                      a                               was half ON when the other upstream OR gate was ON. This
                   0:2n  ½ThOR nom o0:8                   ð10Þ
                          b                      b                               experimental result suggested that the ON signals pushed onto
                              a                     a                            the two input wires of the downstream AND gate (that is, the
              ½ðn  1Þ þ 0:2  ½ThAND nom o0:8n                      ð11Þ    output wires of the two upstream OR gates) were signiﬁcantly
                              b                     b                            different from each other, which was an indication that the
Using b/a ¼ 1.4, we chose a nominal threshold of 0.35  and                      effective concentrations of the two unpuriﬁed gate species that
0.85  for two-input OR and AND gate, respectively, and                          released the output signals were different—one of the gates must
0.4  and 1.6  for three-input OR and AND gate. Experiments                     be an outlier with g/aa0.8.
of the logic gates showed desired behaviours (Fig. 3d and                           Indeed, with a gate calibration experiment shown in Fig. 4b,
Supplementary Fig. 4).                                                           we measured that g18,53/a18,53 ¼ 0.8  for one gate and
   An alternative approach for adjusting the nominal threshold is                g22,53/a22,53 ¼ 0.44  for another. A possible explanation is that
to use the following equations:                                                  the synthesis errors of unpuriﬁed strands somewhat depend on
                                          a                                      DNA sequences30 and variations of effective concentrations may
                        ½ThOR nom ¼0:6                    ð12Þ                 occur between different gate or threshold species. We suspect it
                                          b
                                                                                 was not a coincidence that the outlier gate had a lower effective
                                                         a                       concentration compared with other unpuriﬁed gates, because a
                     ½ThAND nom ¼½ðn  1Þ þ 0:2                       ð13Þ
                                                         b                       particular DNA strand having much worse quality than average is
 Compared with choosing a nominal threshold based on                             probably more likely than it having much better quality.
 the lower and upper bounds, this approach is less ﬂexible but                      Once an outlier is identiﬁed, either a threshold or a gate, the
 simpler.                                                                        nominal concentration can be adjusted using its own threshold to
    Next, we can estimate the ratio between g and a for a gate                   signal ratio (that is, b/a) or gate to signal ratio (that is, g/a), the
 releasing a signal, using an experiment that compares the                       common nominal concentration described in the previous
 fully triggered (tri) concentration of the gate with the signal                 section, and the common ratio for other thresholds and gates:
 when their nominal concentrations are the same.                For example,                               0                aj;i b
                                                                                                       Thj;i:i nom ¼ Thj;i:i nom                 ð17Þ
the data in Fig.  3e showed that G1:1;23 tri ¼0:8 when                                                                       bj;i a
  G1:1;23 nom ¼ w1;23 nom ¼1. Thus, the gate to signal ratio can
be calculated as:                                                                                           0                ai;k g
                                                                                                   Gi:i;k nom ¼ Gi:i;k nom                        ð18Þ
                 g1;23      G1:1;23 eff           w1;23 nom                                                                      gi;k a
                       ¼                               
                 a1;23      G1:1;23 nom            w1;23 eff                        We constructed
                                                                                                  the two-layer
                                                                                                           0         logic circuit using the adjusted
                                                                              nominal gate G22:22;53 nom ¼1=0:440:8¼1:8 (Fig. 4c). The
                            G1:1;23 eff                                        trajectories that compute logic ON reached an ideal high
                       ¼                                               ð14Þ
                             w1;23 eff                                          ﬂuorescence state faster than the previous experiments shown
                                           ½G1:1;23 nom ¼½w1;23 nom
                                                                                 in Fig. 4a and the trajectories that compute logic OFF remained at
                          0:8                                                    a lower ﬂuorescence state that were roughly identical for all three
                       ¼      ¼0:8
                           1                                                     input combinations, regardless of which upstream OR gate was
    Additional gate calibration experiments suggested that the ratio             ON. However, after identifying and adjusting the outlier gate, we
g/a ¼ 0.8 was consistent for different gate and signal molecules                 still had a problem: the OFF trajectories were not at an ideal low

6                                                            NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications

NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373                                                                                                                                                            ARTICLE

                                                              [Th34,18:18]nom = 0.4 ×
 a                                                                                                                     G18:18,53
                                                     x1           34             18                                                     S53
                                                28
                                                   x                                                                            S18     T                         1.0
     x1 110                                     33 2                 3       –0.6     1                                                                                                                    ON
                                                                                                                                                                                                                 x1 x2 x3 x4 x5 y
                       110                         x                                       2                           T*       S18 *   T*                        0.8
     x2 110                                     37 3                                           f                                                                                                                 1 1 1 0 0 0
     x3 100                                                                                            53          5               6




                                                                                                                                                         Output
                                                                                                                                                                  0.6                                            0 1 1 1 0 1
                                       0y                                                                                               y
                                                                                                                                                                                                                 1 0 1 0 1 1
                                                                                                         2      –1.2   1        –1.5                                                                             1 1 0 0 0 0
                                                                                                                                                                  0.4
     x4 001            001                                                                                                  2                                                                              OFF   0 0 1 1 1 1
     x5 001                                          x4                                                                  f                                        0.2
                                                29                39             22                                                                                                                              0 1 0 1 0 1
                                                                                                    [Th53,5:5]nom = 0.85 ×                                                                                       1 0 0 0 1 1
                                                                     2       –0.6     1
                                                                                                                                                                  0.0                                            0 0 0 1 1 0
                                                     x5                                    2                           G22:22,53                                        0    2     4    6      8      10
                                                35                               f                                                      S53
                                                                                                                                                                                  Time (h)
                                                          [Th39,22:22]nom = 0.35 ×                                              S22     T
                                                                                                                       T*       S22 *   T*

 b                                                                                                                                                       c
                                                                                                                                                                            [G22:22,53]′nom = 1.8 ×
  G18:18,53                            18            53                  6                1.0                                                                     1.0                                      ON
                  S53                                                                                                                                                                                            x1 x2 x3 x4 x5 y
                                  x1        x3                                            0.8                                                x1 x2 x3             0.8
          S18     T          34         1                 2        –1.5      y                                                                                                                                   1 1 1 0 0 0
                                                                                 Output




                                                                                                                                                         Output
                                            2
                                                                                          0.6            [G18:18,53]tri = 0.8 ×              0                    0.6                                            0 1 1 1 0 1
     T*   S18 *   T*                             f                                                                                           2                                                                   1 0 1 0 1 1
                                                                                          0.4                                                    0                0.4                                            1 1 0 0 0 0
  G22:22,53                            22            53                6                                 [G22:22,53]tri = 0.44 ×                 2                                                         OFF   0 0 1 1 1 1
                  S53                                                                     0.2                                                                     0.2                                            0 1 0 1 0 1
                                  x2        x3                                                                                                       1
                             39         1                 2        –1.5      y                                                                                    0.0
                                                                                                                                                                                                                 1 0 0 0 1 1
          S22     T
                                            2
                                                                                          0.0                                                                                                                    0 0 0 1 1 0
                                                 f                                              0         1         2            3                                   0       2     4    6       8     10
     T*   S22 *   T*
                                                                                                              Time (h)                                                            Time (h)

Figure 4 | Identifying an outlier gate. (a) Logic circuit diagram, seesaw circuit diagram and experimental data of a two-layer logic circuit. (b) Measuring
the effective concentrations of the gate species. Three independent circuits were used to measure the effective concentrations of two gates fully triggered
by x1 and x2, respectively, comparing with the effective concentration of x3 (using signal strand w18,53). (c) Experimental data of the two-layer logic circuit
using adjusted nominal gate concentration. 1  ¼ 100 nM.



ﬂuorescence state. This led to the next tuning step that is                                                                ON/OFF separation, the range of d can be determined as:
necessary for unpuriﬁed seesaw circuits.                                                                                                                            
                                                                                                                                     yOFF yON ¼0:7  0:3  d  yOFF yON ¼0:9  0:1 ð19Þ

Tuning circuit output. Comparing the behaviour of the AND                                                                  The nominal threshold in the logic gate that produces the circuit
gate when it was in isolation (Fig. 3d) and that when it was                                                               output can then be adjusted accordingly:
connected with two upstream OR gates (Fig. 4c), the ON/OFF                                                                                          0                    a
separation was signiﬁcantly decreased in the latter. These                                                                                    Thj;i:i nom ¼ Thj;i:i nom þ d           ð20Þ
                                                                                                                                                                             b
experimental results suggest that, compared with puriﬁed seesaw
DNA circuits in which the ON/OFF separations were roughly                                                                     Using the data of the two-layer logic circuit shown in Fig. 4c,
identical from a single logic gate to four-layer logic circuits12,                                                         we chose the trajectory with input ¼ 01010 and 11100 as the
unpuriﬁed circuits are much noisier and the behaviour becomes                                                              reference ON and OFF trajectory, respectively, and calculated
less robust with more than one layer. We suspect this is caused by                                                         0.08rdr0.41. We then      increased
                                                                                                                                                             0    the threshold in the down-
the stoichiometry errors in unpuriﬁed gate species. The double-                                                            stream AND gate to Th53;5:5 nom ¼0:85 þ 0:28=1:4¼1:05 and
stranded gate molecules were annealed with the same amount of                                                              repeated the experiment. The circuit behaviour was improved
top and bottom strands, because both strands have combinations                                                             with a much better ON/OFF separation (Fig. 5a).
of toehold and branch migration domains that can cause                                                                        With the same method, we constructed another two-layer logic
undesired interactions with other circuit components and thus                                                              circuit that is composed of an OR gate and two upstream AND
neither should be in excess. However, due to variations in the                                                             gates (Fig. 5b). In this case, using input ¼ 00011 and 01110 as the
pipetting volume and in the accuracy of concentrations, the equal                                                          reference ON and OFF trajectories, we obtained a similar range of
stoichiometry cannot be guaranteed. Without puriﬁcation, a                                                                 d and decided to apply the same amount of increase to the
small excess of one strand or another in the gate species cannot be                                                        threshold in the downstream OR gate.
removed. Therefore, the excess of strands would result in                                                                     It is noteworthy that a rule of thumb is to choose the slowest
undesired release of output signals in logic gates, even without                                                           ON trajectory and the fastest OFF trajectory as the references for
input signals, and introduce extra noise to downstream logic                                                               threshold adjustment, but different choices can be made if one
gates.                                                                                                                     has the knowledge of which data set is experimentally more
   Fortunately, thanks to the thresholding function in every logic                                                         reliable. Also note that increasing the threshold not only
gate, we can tune the circuit output by increasing a threshold.                                                            suppresses the OFF trajectories but also slows down the ON
A simple method for estimating how much threshold adjustment                                                               trajectories and thus this method of tuning the circuit output is
is needed is based on the ON/OFF separation of the circuit                                                                 only applicable if all ON trajectories are signiﬁcantly faster than
output. Using experimental data of a logic circuit with different                                                          all OFF trajectories (which should be true if the thresholds and
inputs, we can choose a trajectory that should compute logic ON                                                            gates are properly calibrated).
and OFF, respectively, and calculate the difference (d) between                                                               Combining the two logic circuits shown in Fig. 5 and adding
the observed OFF value and an ideal OFF value, when the ON                                                                 fan-out gates for input signals that are used in multiple logic
trajectory reaches an ideal ON value. Considering 0.7 and 0.3 as                                                           gates, we successfully demonstrated the rule 124 sub-circuit
the lower bound, and 0.9 and 0.1 as the upper bound for an ideal                                                           consisting of 54 distinct DNA species (Supplementary Fig. 6).

NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications                                                                                                                                    7

ARTICLE                                                                                                                     NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373



    a
                                        [Th34,18:18]nom = 0.4×
                                                                                                                                  1.0 1.0
                                       x1        34          18                                                                         0.8                                                ON
                                  28                                                                                                    0.6
                                       x2                                                                                         0.8 0.4
                                  33                   3   –0.6   1                                                                                                                              x1 x2 x3 x4 x5   y
                                                                                                                                        0.2
    x1                                 x3                              2                                                                                                                         1 1 1 0 0        0
                                  37                                                                                              0.6 0.00




                                                                                                                         Output
    x2                                                                     f                                                                      2   4       6   8   10                         0 1 1 1 0        1
    x3                                                                           53          5                 6
                                                                                                                                                                                                 1 0 1 0 1        1
                            y                                                                                                     0.4                                                            1 1 0 0 0        0
                                            [G22,22:53]′nom = 1.8×                    2   –1.2   1           –1.5
                                                                                                                    y
                                                                                                     2
                                                                                                                                                                                                 0 0 1 1 1        1
    x4
                                                                                                         f                        0.2                                                            0 1 0 1 0        1
    x5                                 x4         39          22                                                                                                                           OFF
                                  29                                                                                                                                                             1 0 0 0 1        1
                                                                               [Th53,5:5]′nom = 1.05×                                                                                            0 0 0 1 1        0
                                                                                                                                  0.0
                                                       2   –0.6    1
                                       x5                              2                                                                0                 5              10      15   20
                                  35                                       f                                                                                          Time (h)
                                            [Th39,22:22]nom = 0.35 ×


    b                                       [Th36,21:21]nom = 1.6 ×
                                                                                                                                  1.0
                                                                                                                                        1.0
                                       x1        36          21
                                  29                                                                                                    0.8
                                                                                                                                  0.8 0.6                                                  ON
                                       x2
                                  35                3      –2.2   1                                                                     0.4                                                      x1 x2 x3 x4 x5 y
    x1                                 x3                              2                                                                0.2
    x2                            38                                                                                              0.6   0.0                                                      0 0 0 1 1 1
                                                                           f




                                                                                                                        Output
    x3                                                                           10          1                 23                             0   2   4       6   8   10                         1 0 0 0 1 0
                            y                                                                                                                                                                    0 1 0 1 0 0
                                                                                      2   –0.6   1           –1.5   y             0.4                                                            0 0 1 1 1 1
    x4                                                                                               2                                                                                           1 1 0 0 0 0
    x5                                 x4                                                                f                        0.2                                                            1 0 1 0 1 0
                                  28              40          27                                                                                                                           OFF
                                                                               [Th10,1:1]′nom = 0.55×                                                                                            0 1 1 1 0 0
                                                                                                                                                                                                 1 1 1 0 0 1
                                                      2    –1.2    1                                                              0.0
                                       x5                              2                                                                0                 5              10      15   20
                                  33                                 f
                                                                                                                                                                      Time (h)
                                              [Th40,27:27]nom = 0.85 ×

Figure 5 | Tuning circuit output. Logic circuit diagram, seesaw circuit diagram and experimental data of a two-layer logic circuit with (a) two upstream OR
gates connected to a downstream AND gate and (b) two upstream AND gates connected to a downstream OR gate. Nominal concentrations shown in grey
and black indicate adjustments made in a previous step and in this step, respectively. Small insets of experimental data show the circuit behaviours before
adjustments. 1  ¼ 100 nM.


  We do not have evidence of how well unpuriﬁed circuits with                                        behaviour. Continue to construct a larger circuit. If it fails to
multiple layers can be constructed, but we suspect that with the                                     compute correctly, the most likely reason would be a new outlier
same amount of threshold increase (that is, d  a/b) in all logic                                    gate. Identify the outlier based on cases where the ON/OFF
gates at layer two and above, undesired signals released from                                        separation is worst, and repeat the steps for calibrating the gate
upstream gates can be effectively suppressed at every layer                                          accordingly.
without accumulating over an increasing number of layers.                                               Following the ﬂowchart, we completed the construction of the
                                                                                                     rule 110 sub-circuit in only 3 days (Fig. 6). If all components were
                                                                                                     PAGE puriﬁed, incrementally building the circuit would require
Systematic procedure. Starting from the calibration of effective                                     at least one additional day for each new experiment, assuming no
concentrations for threshold and gate species in general, to the                                     experimental errors. The turnaround time would be signiﬁcantly
identiﬁcation and adjustment of any outliers, and then to the ﬁnal                                   increased.
tuning of circuit output, we established three sequential steps for                                     Combining the components from both rule 110 and rule 124
building unpuriﬁed seesaw circuits. To make these steps easy to                                      sub-circuits, using shared input-fanout gates and a three-input
follow, we now further describe a systematic procedure, and                                          NAND gate (Fig. 2ab), the full rule 110–124 circuit consisting of
evaluate the procedure by constructing a new logic circuit from                                      78 distinct DNA species was constructed in one test tube. The
scratch—the rule 110 sub-circuit.                                                                    ﬂuorescence kinetics experiments showed correct ON and OFF
   We summarized the procedure in a ﬂowchart (Fig. 6). It starts                                     states of the two pairs of dual-rail outputs, for all eight possible
with constructing the simplest functional component, digital                                         inputs (Fig. 7a). To pictorially compare the ideal logic behaviour
signal restoration, and estimating the effective threshold com-                                      and the DNA circuit behaviour, we plotted each output into an
pared to a signal. If the threshold to signal ratio b/a41.2, adjust                                  array that represents eight cellular automata generations (Fig. 7b).
the nominal thresholds in all logic gates. Next, construct a single                                  The ideal logic circuit behaviour corresponds to four images of
logic gate. If it fails to compute correctly, it indicates that the                                  dogs. The DNA circuit behaviour yielded less contrast between
threshold species in this logic gate is an outlier, and thus one                                     the dogs and their backgrounds, but the patterns were still clearly
needs to go back to the ﬁrst step and repeat the process to                                          recognizable.
calibrate this particular threshold. Otherwise, move on to gate
calibration experiments. If the gate to signal ratio g/ao0.8, adjust
all nominal gates.                                                                                   Modelling. Despite that the experiments were performed at a
   Then construct a two-layer logic circuit, and identify if there                                   higher concentration (that is, 1  ¼ 100 nM), the rule 110–124
exists an outlier gate. If so, repeat the process to calibrate this                                  circuit computed much slower than what the simulations pre-
particular gate. At this point, the circuit still may not exhibit                                    dicted for 1  ¼ 50 nM (Fig. 2c). We suspect that the difference
desired ON/OFF separation (for example, the OFF trajectories                                         was caused by the impurity of the molecules. To better predict the
may be higher than 0.3 when the ON trajectories reach 0.7).                                          behaviour of seesaw circuits using unpuriﬁed components, we
However, if the ON trajectories are signiﬁcantly faster than the                                     developed a model that takes synthesis errors into consideration.
OFF trajectories, increase the nominal threshold in the logic gate                                      We ﬁrst deﬁne the probability of having n errors in a
that directly produces the circuit output to tune the circuit                                        chemically synthesized DNA strand of l bases, given that r is the

8                                                                      NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications

NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373                                                                                                                                                                                                                             ARTICLE

             1.0                                                                                                                                                                                                          1.0
                                                                                                                                             N                                                                                                                               ON
             0.8                                                                                          Start                                               /  < 0.8?                                                                                                          x1 x2 x3 x4 x5
                       [Th43,30:30]sim = 0.7 ×                    Input                                                                                                                                                   0.8
                                                                                                                                                                                                                                                                                   0 00 11
    Output

             0.6                                                   0                                                                                                         Y




                                                                                                                                                                                                                 Output
                       [Th43,30:30]nom = 0.5 ×                                                                                                                                                                            0.6                                                      10011
             0.4                                                   0.3                      Digital signal restoration                                 Adjust nominal gate                                                                                                         01001
                                                                   0.7                                                                                                                                                    0.4                                                      00110
             0.2                                                                                                                                                                                                                                                             OFF
                                                                   1                                                                                                                                                      0.2                                                      10110
             0.0                                                                      Estimate effective threshold                                    Two-layer logic circuits                                                                                                     01100
                0          2         4    6        8         10                                                                                                                                                           0.0                                                      11100
                                    Time (h)                                                                                                                                                                                    0           2      4         6          8
                                                                                                                                             Y
                                                                                                                            N                                Outlier gate?                                                                      Time (h)
     Apply equation 7:                                                                               /  > 1.2?
                                                                                                                                                                             N                            Apply equations 19 and 20
                                                                                                                                                                                                                                  :
      43,30                   [W43,30]nom                                                                    Y
                                                       0.7
                       =                       =             = 1.4
       43,30              [Th43,30:30]nom             0.5                                  Adjust nominal threshold                                    y
                                                                                                                                                            OFF                                   Y       0.08 = yOFF            – 0.3 ≤ δ ≤ yOFF ON        – 0.1 = 0.48
                                                                                                                                                                  yON= 0.7 ≤ 0.3?                                        yON= 0.7                   y =0.9
                                                                                                                                                                                                                                                      
                                                                                                                                                                                                          [Th43,30:30]′ nom = [Th43,30:30]nom +  × = 0.55 ×
     Apply equations 10 and 11 for n = 2:                                                                                                                                    N                                                                        
                                                                                                    Logic gates
                                                                                                                                               Adjust nominal threshold                                                                           
      0.28 = 0.4 ×   ≤ [ThOR]nom = 0.8 × = 0.57                                                                                                                                                           [Th44,31:31]′ nom = [Th44,31:31]nom +  ×    = 1.05 ×
                                                                                                                                                                                                                                                  
                                                                                                      Outlier               Y
                                                                                                                                                          Larger circuits
      0.85 = 1.2 ×                 ≤ [ThAND]nom < 1.6 ×   = 1.14                                    threshold?
                                                                                                                                                                                                                         L0
                                                                                                              N                                                                                                            C0
                                                                                                                                                              Correct                             N                        L1                                                                  0
             1.0                                                                                                                                                                                                                                                                        R110
                                                                                             Measure effective gate                                         computation?                                                   C1
             0.8                                                  x1x2
                                                                                                                                                                             Y                                                                                                          R110
                                                                                                                                                                                                                                                                                               1
                                                                     00
    Output




             0.6
                                                                     01                                                                                              End                                                   R1
                                                                                            1.0
             0.4                                                     10
                       [Th43,30:30]nom = 0.35 ×                                             0.8                                                                                                                            R0
             0.2                                                     11
                                                                                   Output




                                                                                            0.6                                      W43,30 W30,24                          1.0
             0.0                                                                                     [G30,30:24]tri = 0.8 ×                                                           R1100                                                 R110
                                                                                                                                                                                                                                                1                                        LCR
             1.0                                                                            0.4                                          0   0                                                                                                                                            000
                                                                                                                                                                            0.8
                                                                                            0.2                                          2   0                                                                                                                                            100
             0.8                                                  x1x2




                                                                                                                                                                   Output
                                                                                                                                         0   1                              0.6                                                                                                           010
                                                                                            0.0
    Output




             0.6                                                  00                                                                                                                                                                                                                      001
                                                                                              0.0   0.2     0.4 0.6     0.8     1.0                                         0.4
                                                                  01                                                                                                                                                                                                                      110
             0.4                                                                                            Time (h)
                       [Th44,31:31]nom = 0.85 ×                   10                                                                                                        0.2
                                                                                                                                                                                                                                                                                          101
                                                                                        Apply equation 14:                                                                                                                                                                                011
             0.2
                                                                  11                    30,24   [G30:30,24]eff 0.8                                                         0.0                                                                                                           111
             0.0                                                                               =               =    = 0.8
                   0       2         4    6        8         10                         30,24    [W30,24]eff    1                                                                0           5          10         15               20 0           5     10            15         20
                                    Time (h)                                                                                                                                                          Time (h)                                          Time (h)


Figure 6 | Flowchart for building seesaw DNA circuits using unpuriﬁed components. Insets show how the ﬂowchart was used to construct the rule 110
sub-circuit. Y (yes) and N (no) highlighted in orange in the ﬂowchart indicate the situations encountered and decisions made while building the rule 110
sub-circuit. 1  ¼ 100 nM.


    a                                   R124
                                               1
                                                                                                             R1240                                                                      R1101                                                              R1100
                                                                                                                                                                                                                                                                                         LCR
             1.0                                                                   1.0                                                                 1.0                                                                           1.0
                                                                                                                                                                                                                                                                                          000
             0.8                                                                   0.8                                                                 0.8                                                                           0.8                                                  001
                                                                                                                                                                                                                                                                                          010
                                                                          Output




                                                                                                                                             Output




                                                                                                                                                                                                                            Output
    Output




             0.6                                                                   0.6                                                                 0.6                                                                           0.6
                                                                                                                                                                                                                                                                                          011
             0.4                                                                   0.4                                                                 0.4                                                                           0.4                                                  100
                                                                                                                                                                                                                                                                                          101
             0.2                                                                   0.2                                                                 0.2                                                                           0.2
                                                                                                                                                                                                                                                                                          110
             0.0                                                                   0.0                                                                 0.0                                                                           0.0                                                  111
                       0        5       10     15            20                              0      5        10        15       20                            0              5          10        15      20                                0       5      10      15        20
                                        Time (h)                                                             Time (h)                                                                  Time (h)                                                            Time (h)


    b                                                                                                                                                                                                                                                                                          1.0
                                                                                                                                                                                                                                                                                               0.8
                                                                                                                                                                                                                                                                                               0.6
                                                                                                                                                                                                                                                                                               0.4
                                                                                                                                                                                                                                                                                               0.2
                                                                                                                                                                                                                                                                                               0

Figure 7 | Implementing the rule 110–124 full circuit. (a) Fluorescence kinetics data of the two pairs of dual-rail outputs. 1  ¼ 100 nM. All DNA
sequences are listed in Supplementary Table 1. (b) Comparing the ideal logic circuit behaviour (left) with the DNA circuit behaviour (right). Each of the
circuit outputs is illustrated by an array of 7  8 cells, representative of eight cellular automata generations on a torus with starting conﬁguration
(0,0,0,1,0,0,0). The arrays for the DNA circuit were plotted using the output values at 24 h from the data. The ideal logic circuit behaviour corresponds to
an image of a black dog with a white background for R1241, an inverted image for R1240 and their mirror images for R1101 and R1100, respectively.


probability of synthesis error per base:                                                                                                                locations, we treat the very small population of molecules with
                                                                                                                                                      more than one synthesis error as non-reactive, and classify the
                               l                                                                                                                        remaining molecules containing a single synthesis error based on
                  Pðr; l; nÞ¼      ð1  r Þl  n r n                                                                                ð21Þ
                               n                                                                                                                        the domain where the error occurs. For example, a signal strand is
                                                                                                                                                        composed of two branch migration domains ﬂanking a toehold
We then calculate the populations of signal, gate and threshold                                                                                         domain. Given that a branch migration domain has 15 bases and
molecules with and without synthesis errors (Fig. 8a). To make                                                                                          a toehold domain has 5 bases, the probability of a signal strand
the model simple enough, but accurate enough to describe                                                                                                having s errors in a speciﬁc branch migration domain (and thus
reactions that involve molecules with synthesis errors at distinct                                                                                      not in the other) and t errors in the toehold domain can be

NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications                                                                                                                                                                                                     9

ARTICLE                                                                                                                                                                         NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373



     a
                           wj,i                                   wj ,i                               wj , i                                      wj,i                                                         Thj,i:i                                                   Thj, i:i
                  Sj                                         Sj     *                       Sj            *                                 Sj            *                                                                                                                  * Si
                                                                                                                                                                                                                            Si
                       T            Si                            T         Si                    T               Si                              T             Si
                                                                                                                                                                                                       Sj* T*               Si*                               Sj*    T*          Si*

                 Pw (r, 0,0) = 70.3%                   Pw (r, 1,0) = 10.7%                 Pw (r, 0,1) = 3.6%                             Pw (r, 1,0) = 10.7%                                          PTh(r, 0) = 90.4%                                       PTh(r, 1) = 9.1%


                           Gi:i,k                                      Gi:i ,k                             Gi:i, k                                            Gi:i,k                                       G i:i,k                                                        Gi :i,k
                                             Sk                            *          Sk                        *                Sk                                     *            Sk                     *                        Sk                                     *              Sk

                       Si                T                            Si         T                         Si               T                                 Si                T                          Si                  T                                          Si           T

            T*         Si*           T*                 T*            Si*        T*        T*              Si*              T*               T*           Si*                   T*                T*       Si*                 T*                         T*             Si*          T*

           PG (r, 0,0) = 63.6%                         PG (r, 1,0) = 9.6%                  PG (r, 0,1) = 3.2%                               PG (r, 1,0) = 9.6%                                   PG (r, 0,1) = 3.2%                                       PG (r, 0,1) = 3.2%


     b
                                                  Without synthesis errors                                                                                                  With synthesis errors

                                                                                                          wj,i                                          Gi:i,k                            ks ⁄ 100                          Gj,i :i                                             wi,k
                                                                ks                           Sj
                                                                                                                 *                                                               Sk                       Sj                    *                                                                Sk
     Seesawing reactions                          wj,i + Gi:i,k →
                                                                ← Gj,i:i + wi,k
                                                                                                                                      +                                                                                                                        +
                                                                                                      T              Si                                  Si                 T                                    T                  Si
                                                                ks                                                                                                                                                                                                              Si          T
                                                                                                                                                                                             ks
                                                                                                                                           T*            Si*            T*                                       T*                 Si*              T*

                                                                                                          wj, i                                       Thj,i:i                                                               Waste                                              Waste
                                                                      kf                                     *                                                                            kf ⁄ 100         Sj
                                                                                             Sj                                       +                                                                                                                        +
     Thresholding reactions                            wj,i + Thj,i:i → ∅                                                                                          Si                                                      T                  Si                                Si
                                                                                                      T              Si
                                                                                                                                           Sj* T*               Si*                                              Sj* T*                       Si*


                                                                                                          wj, i                                       Repi                                                                     Fluori                                          Waste
                                                               2ks                           Sj
                                                                                                             *                                                                            ks ⁄ 50                Sj
      Reporting reactions                                                                                                             +                                                                                                                        +
                                                    wj,i + Repi → Fluori                                                                                 Si
                                                                                                                                                                            Q
                                                                                                                                                                                                                      T                  Si                                     Si
                                                                                                                                                                                                                                                                                           Q
                                                                                                      T              Si                                                     F                                                                             F
                                                                                                                                           T*           Si*                                                           T*              Si*


                                                                                                  wi,x                                                   Gi:i , k                                                          wi ,k                                                 Gi:i,x
                                                                kl                                                     Sx
                                                                                                                                                             *                   Sk         2kl                              *                                                                   Sk
          Leak reactions                                                                                                              +                                                                                                        Sk              +
                                                  wi,x + Gi:i,k → wi,k + Gi:i,x                                                                          Si             T                                                                                                       Si          T
                                                                                                 Si              T                                                                                                    Si                  T
                                                                                                                                           T*           Si*             T*                                                                                          T*          Si*         T*

                                                                                                          wx,y                                         G i:i,k                                                                                                            Gx,y: i :i,k
                                                                kf                                                                                      *                        Sk         kf            Sx          Sy                                  Sk                   *
                                                  wx,y + Gi:i,k →
                                                                ← Gx,y:i:i,k
                                                                                            Sx                                        +
                                                                                                                                                         Si             T                                        T                  Si               T
                                                                krf                                   T           Sy                                                                       10krf
         Universal toehold                                                                                                                 T*           Si*             T*                                       T*                 Si*              T*
         binding reactions
                                                                 kf                                       wx,y                                    Thj, i:i                                  kf                                                     Thx,y:j, i:i
                                                                                                                                                      *                                                   Sx               Sy                              *
                                                  wx,y + Thj,i:i →
                                                                                            Sx                                        +
                                                                 ← Thx,y:j,i:i                                                                                     Si                                             T                  Si
                                                                 krs                                  T              Sy                                                                    10krs
                                                                                                                                           Sj* T*               Si*                                       Sj* T*                     Si*


Figure 8 | A model for unpuriﬁed seesaw circuits. (a) Populations of signal, gate and threshold molecules without and with synthesis errors in the marked
locations. r ¼ 0.01. (b) Example reactions that involve DNA strands without and with synthesis errors. 8i, j, k, x and y.

calculated as:                                                                                                                               network, involving all populations of defective molecules (Fig. 8b
                                                                                                                                             and Supplementary Note 1).
                    Pw ðr; s; t Þ¼Pðr; 15; sÞPðr; 5; t ÞPðr; 15; 0Þ                                                            ð22Þ           We ﬁrst simulated the rule 110–124 circuit assuming that all
   In a previous study on the robustness of a catalytic DNA strand                                                                           molecules do not have synthesis errors, at the concentrations used
displacement motif21, a single base mutation in an invading                                                                                  in the experiments (Fig. 9a). Using exactly the same concentra-
strand signiﬁcantly slowed down (on the scale of 100 fold) a                                                                                 tions for all species, and the same rate parameters for reactions
reversible strand displacement reaction that was designed with                                                                               that are not affected by synthesis errors, we then simulated the
DG°E0, both when the mutation was in the toehold and when it                                                                                 circuit with each species divided into multiple populations
was in the branch migration domain. In contrast, an irreversible                                                                             including synthesis errors (Fig. 9b). The results of these two
strand displacement reaction was only slowed down signiﬁcantly                                                                               simulations were dramatically different: only the latter exhibited a
(also on the scale of 100-fold) when the mutation was in the                                                                                 remarkable degree of agreement with the data shown in Fig. 7a.
toehold domain, but the reaction rate remained roughly
unchanged when the mutation was in the branch migration                                                                                      Discussion
domain.                                                                                                                                      The biggest challenge that could prevent a molecular compiler
   These observations lead us to the following interpretations:                                                                              from working in practice is that a new circuit may require new
A synthesis error in the toehold domain can slow down strand                                                                                 molecular components, which may not behave the same as the
displacement by increasing the disassociation rate of the toehold                                                                            ones previously characterized. Thus, what made it possible to
and thus decreasing the overall reaction rate. A synthesis error in                                                                          build a new complex circuit using the Seesaw Compiler? First,
the branch migration domain can also slow down strand                                                                                        there are only three types of molecular components (signal, gate
displacement, but only when the energy change caused by the                                                                                  and threshold) for arbitrary feedforward logic circuits, which
synthesis error is signiﬁcant compared to the designed standard                                                                              yield highly predictable circuit behaviour. Second, because of the
free energy of the reaction, and not when the reaction is already                                                                            simplicity of the molecules, there is minimal sequence design
strongly favoured in one direction. Based on these interpretations,                                                                          challenge. A three-letter code (A, T and C) for all signal strands is
we estimated the rates of all ﬁve types of reactions in a seesaw                                                                             sufﬁcient to eliminate undesired reactions. Finally, exact kinetics

10                                                                                               NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications

NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373                                                                                                             ARTICLE

 a                        R1241                                 R1240                                  R1101                                      R1100
           1.0                                    1.0                                    1.0                                        1.0                             LCR
           0.8                                    0.8                                    0.8                                        0.8                             000
                                                                                                                                                                    001




                                                                                Output




                                                                                                                           Output
                                         Output
  Output




           0.6                                    0.6                                    0.6                                        0.6                             010
                                                                                                                                                                    011
           0.4                                    0.4                                    0.4                                        0.4                             100
           0.2                                    0.2                                    0.2                                        0.2                             101
                                                                                                                                                                    110
           0.0                                    0.0                                    0.0                                        0.0                             111
                 0   5    10 15     20                  0   5   10 15      20                  0   5    10 15     20                      0   5    10 15     20
                         Time (h)                               Time (h)                               Time (h)                                   Time (h)

 b                        R1241                                  R1240                                 R1101                                      R1100
           1.0                                    1.0                                    1.0                                        1.0                             LCR
           0.8                                    0.8                                    0.8                                        0.8                             000
                                                                                                                                                                    001
  Output




                                         Output




                                                                                Output




                                                                                                                           Output
           0.6                                    0.6                                    0.6                                        0.6                             010
                                                                                                                                                                    011
           0.4                                    0.4                                    0.4                                        0.4                             100
           0.2                                    0.2                                    0.2                                        0.2                             101
                                                                                                                                                                    110
           0.0                                    0.0                                    0.0                                        0.0                             111
                 0   5   10 15      20                  0   5   10 15      20                  0   5   10 15      20                      0   5   10 15      20
                         Time (h)                               Time (h)                               Time (h)                                   Time (h)

Figure 9 | Simulations comparing the puriﬁed and unpuriﬁed models. (a) Simulations of the rule 110–124 circuit using the previously developed model for
puriﬁed seesaw circuits, predicting that the circuit should yield desired outputs in roughly 8 h (shown as dotted lines) and the undesired reactions will take
over in 24 h. (b) Simulations using the new model for unpuriﬁed seesaw circuits, predicting that the circuit should yield desired outputs in roughly 24 h.
kf ¼ 2  106 M  1 s  1, ks ¼ 5  104 M  1 s  1, kl ¼ 10 M  1 s  1, krf ¼ 26 s  1, krs ¼ 1.3 s  1. 1  ¼ 100 nM.

is not essential for qualitatively correct computation and thus                           species were purchased unpuriﬁed (standard desalting). The reporter strands with
small difference caused by DNA sequences should not affect the                            ﬂuorophores and quenchers were purchased puriﬁed (HPLC). All strands were
                                                                                          purchased at 100 mM in TE buffer pH 8.0 and stored at 4 °C.
desired circuit behaviour.
   On the other hand, the biggest challenge that could prevent us
from using unpuriﬁed DNA strands is that the synthesis errors                             Annealing protocol and buffer condition. Gate complexes were annealed
                                                                                          together at 20 mM, with equal stoichiometry of top and bottom strands. Threshold
may lead to completely unpredictable molecular behaviours.                                and reporter complexes were annealed together at 20 mM with a 20% excess of top
Thus, what made it possible to build a complex circuit using                              strands. All DNA complexes were annealed in 1  TE buffer with 12.5 mM Mg2 þ ,
unpuriﬁed strands? First, the Seesaw Compiler provides simula-                            prepared from 100  TE pH 8.0 (Fisher BioReagents) and 1 M MgCl2 (Invitrogen).
tions as a debugging tool and makes it straightforward to identify                        Annealing was performed in a thermal cycler (Eppendorf), ﬁrst heating up to 90 °C
problems caused by the synthesis errors. Second, again because                            for 2 min and then slowly cooling down to 20 °C at the rate of 6 s per 0.1 °C. All
                                                                                          annealed complexes were stored at 4 °C.
there are only three types of species, it is relatively easy to
understand the behaviours of defective molecules, as we expect
similar synthesis quality across distinct species of the same type.                       Fluorescence spectroscopy. Fluorescence kinetics data in Figs 3–6 and
                                                                                          Supplementary Figs 3–6 were collected every 2 min in a monochromator-based
More importantly, the signal restoration built in to every logic                          plate reader (Synergy H1M, BioTek). Experiments were performed with 100 ml
gate allows simple tuning to restore desired circuit behaviour,                           reaction mixture per well, in 96-well microplates (black with clear ﬂat bottom,
compensating for the impurity of molecules.                                               polystyrene NBS, Corning 3651) at 25 °C. Clear adhesive sealing tapes (Thermo
   In general, there are several factors that we ﬁnd important for                        Scientiﬁc Nunc 232701) were used to prevent evaporation. The excitation/emission
                                                                                          wavelengths were set to 497/527 nm for ATTO 488 and 597/629 nm for ATTO 590.
the goals of producing a better molecular compiler, and                                      Fluorescence kinetics data in Fig. 7 were collected every 4 min in a
implementing unpuriﬁed DNA circuits with more robust                                      spectroﬂuorimeter (Fluorolog-3, Horiba). Experiments were performed with 500 ml
behaviours. Given that it is difﬁcult to obtain fully predictable                         reaction mixture per cuvette, in ﬂuorescence cuvettes (Hellma 115 F-QS) at 25 °C.
behaviour for newly designed molecular components, alternative                            The excitation/emission wavelengths were set to 502/522 nm for ATTO 488, 602/
                                                                                          624 nm for ATTO 590, 560/575 nm for ATTO 550 and 649/662 nm for ATTO 647.
architectures that enable arbitrary circuits to be created from a                         Both excitation and emission bandwidths were set to 2 nm and the integration time
constant number of molecules will likely promote the develop-                             was 10 s for all experiments.
ment of compilers that work reliably in these contexts31. It is also
necessary to eliminate leak reactions in DNA circuits32 and to                            Data analysis. A Mathematica Notebook ﬁle for data analysis and example data
improve the building blocks such that they are substantially less                         ﬁles are available to download at the Seesaw Compiler website: http://qianlab.cal-
sensitive to synthesis errors and stoichiometry errors.                                   tech.edu/SeesawCompiler/DataAnalysis.php.
   Nonetheless, with an experimental validation of the Seesaw
Compiler and simpliﬁed experimental procedures using unpur-                               Data availability. Key data supporting the ﬁndings of this study are available to
iﬁed DNA strands described in this work, it is now possible to                            download at the Seesaw Compiler website and all other data are available from the
imagine a near future in which a molecular compiler can generate                          corresponding author upon reasonable request.
protocols from a high-level circuit function, and the protocols can
then be executed by a liquid handling robot. Molecular engineers                          References
typing away on a computer to create biochemical circuits in a test                        1. Zhang, D. Y. & Seelig, G. Dynamic DNA nanotechnology using strand-
tube is no longer just a distant dream.                                                      displacement reactions. Nat. Chem. 3, 103–113 (2011).
                                                                                          2. Zadeh, J. N. et al. NUPACK: analysis and design of nucleic acid systems.
                                                                                             J. Comput. Chem. 32, 170–173 (2011).
Methods                                                                                   3. Lakin, M. R., Youssef, S., Polo, F., Emmott, S. & Phillips, A. Visual DSD:
DNA oligonucleotide synthesis. DNA oligonucleotides were purchased from                      a design and analysis tool for DNA strand displacement systems.
Integrated DNA Technologies (IDT). The DNA strands in gate, threshold and fuel               Bioinformatics 27, 3211–3213 (2011).

NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications                                                                          11

ARTICLE                                                                                               NATURE COMMUNICATIONS | DOI: 10.1038/ncomms14373



4. Zuker, M. Mfold web server for nucleic acid folding and hybridization               28. Wolfram, S. Statistical mechanics of cellular automata. Rev. Mod. Phys. 55, 601
    prediction. Nucleic Acids Res. 31, 3406–3415 (2003).                                   (1983).
5. Gruber, A. R., Lorenz, R., Bernhart, S. H., Neuböck, R. & Hofacker, I. L. The      29. Cook, M. Universality in elementary cellular automata. Complex Syst. 15, 1–40
    Vienna RNA websuite. Nucleic Acids Res. 36, W70–W74 (2008).                            (2004).
6. Schaeffer, J. M., Thachuk, C. & Winfree, E. Stochastic simulation of the            30. Integrated DNA Technologies. Chemical Synthesis and Puriﬁcation of
    kinetics of multiple interacting nucleic acid strands. LNCS 9211, 194–211              Oligonucleotides, https://www.idtdna.com/pages/docs/technical-reports/
    (2015).                                                                                chemical-synthesis-of-oligonucleotides.pdf (2005).
7. Lakin, M. R., Parker, D., Cardelli, L., Kwiatkowska, M. & Phillips, A. Design       31. Qian, L. & Winfree, E. Parallel and scalable computation and spatial dynamics
    and analysis of DNA strand displacement devices using probabilistic model              with DNA-based chemical reaction networks on a surface. LNCS 8727,
    checking. J. R. Soc. Interface 9, 1470–1485 (2012).                                    114–131 (2014).
8. Lakin, M. R., Phillips, A. & Stefanovic, D. Modular veriﬁcation of DNA              32. Thachuk, C., Winfree, E. & Soloveichik, D. Leakless DNA strand displacement
    strand displacement networks via serializability analysis. LNCS 8141, 133–146          systems. LNCS 9211, 133–153 (2015).
    (2013).
9. Grun, C., Sarma, K., Wolfe, B., Shin, S. W. & Winfree, E. A domain-level DNA
    strand displacement reaction enumerator allowing arbitrary non-
                                                                                       Acknowledgements
                                                                                       A.J.T. was supported by an NSF grant (1351081) and an NSF expedition in computing
    pseudoknotted secondary structures. Preprint at https://arxiv.org/abs/
                                                                                       (1317694). C.T. was supported by a Banting Fellowship. L.Q. was supported by a Career
    1505.03738 (2015).
                                                                                       Award at the Scientiﬁc Interface from the Burroughs Wellcome Fund (1010684) and a
10. Shin, S. W., Thachuk, C. & Winfree, E. Verifying chemical reaction
                                                                                       Faculty Early Career Development Award from NSF (1351081). All other authors were
    network implementations: a pathway decomposition approach. Preprint at
                                                                                       supported by Innovation in Education funds from the Provost’s Ofﬁce at the California
    https://arxiv.org/abs/1411.0782 (2014).
                                                                                       Institute of Technology, through a class BE/CS 196—Design and Construction of Pro-
11. Johnson, R. F., Dong, Q. & Winfree, E. Verifying chemical reaction network
                                                                                       grammable Molecular Systems.
    implementations: a bisimulation approach. LNCS 9818, 114–134 (2016).
12. Qian, L. & Winfree, E. Scaling up digital circuit computation with DNA strand
    displacement cascades. Science 332, 1196–1201 (2011).                              Author contributions
13. Grun, C., Werfel, J., Zhang, D. Y. & Yin, P. DyNAMiC workbench: an                 C.T. designed the logic circuit. C.T., J.B., R.F.J. and D.A.A. designed the DNA circuit,
    integrated development environment for dynamic DNA nanotechnology. J. R.           performed the experiments and analysed the data of the rule 124 sub-circuit. K.M.C.
    Soc. Interface 12, 20150580 (2015).                                                designed and performed the experiments, and analysed the data for gate calibration.
14. Yin, P., Choi, H. M. T., Calvert, C. R. & Pierce, N. A. Programming                A.J.T. designed and performed the experiments and analysed the data of the full circuit
    biomolecular self-assembly pathways. Nature 451, 318–322 (2008).                   and led the project to completion. C.T. and L.Q. developed the model. A.J.T., C.T. and
15. Rothemund, P. W. K. Folding DNA to create nanoscale shapes and patterns.           L.Q. wrote the manuscript. L.Q. initiated and guided the project.
    Nature 440, 297–302 (2006).
16. Tørring, T., Voigt, N. V., Nangreave, J., Yan, H. & Gothelf, K. V. DNA origami:
    a quantum leap for self-assembly of complex structures. Chem. Soc. Rev. 40,        Additional information
    5636–5646 (2011).                                                                  Supplementary Information accompanies this paper at http://www.nature.com/
17. Saccà, B. & Niemeyer, C. M. DNA origami: the art of folding DNA. Angew.           naturecommunications
    Chem. Int. Ed. 51, 58–66 (2012).
18. Kearney, C. J., Lucas, C. R., O’Brien, F. J. & Castro, C. E. DNA origami: folded   Competing ﬁnancial interests: The authors declare no competing ﬁnancial
    DNA-nanodevices that can direct and interpret cell behavior. Adv. Mater. 28,       interests.
    5509–5524 (2016).
19. Chandrasekaran, A. R., Anderson, N., Kizer, M., Halvorsen, K. & Wang, X.           Reprints and permission information is available online at http://npg.nature.com/
    Beyond the fold: emerging biological applications of DNA origami.                  reprintsandpermissions/
    ChemBioChem 17, 1081–1089 (2016).
                                                                                       How to cite this article: Thubagere, A. J. et al. Compiler-aided systematic construction
20. Zhang, D. Y. Cooperative hybridization of oligonucleotides. J. Am. Chem. Soc.
                                                                                       of large-scale DNA strand displacement circuits using unpuriﬁed components.
    133, 1077–1086 (2010).
                                                                                       Nat. Commun. 8, 14373 doi: 10.1038/ncomms14373 (2017).
21. Zhang, D. Y. & Winfree, E. Robustness and modularity properties of a
    non-covalent DNA catalytic reaction. Nucleic Acids Res. 38, 4182–4197 (2010).      Publisher’s note: Springer Nature remains neutral with regard to jurisdictional claims in
22. Qian, L. & Winfree, E. A simple DNA gate motif for synthesizing large-scale        published maps and institutional afﬁliations.
    circuits. J. R. Soc. Interface 8, 1281–1297 (2011).
23. Qian, L., Winfree, E. & Bruck, J. Neural network computation with DNA strand
    displacement cascades. Nature 475, 368–372 (2011).                                                   This work is licensed under a Creative Commons Attribution 4.0
24. Qian, L. Seesaw Compiler, http://www.qianlab.caltech.edu/SeesawCompiler/                             International License. The images or other third party material in this
    (2011).                                                                            article are included in the article’s Creative Commons license, unless indicated otherwise
25. Müller, D. E. Asynchronous Logics and Application to Information Processing,      in the credit line; if the material is not included under the Creative Commons license,
    Switching Theory in Space Technology (Stanford University Press, 1963).            users will need to obtain permission from the license holder to reproduce the material.
26. Lakin, M. et al.Visual DSD, https://www.microsoft.com/en-us/research/project/      To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/
    programming-dna-circuits/ (2009).
27. Soloveichik, D. CRNSimulator, http://users.ece.utexas.edu/~soloveichik/
    crnsimulator.html (2009).                                                          r The Author(s) 2017




12                                                              NATURE COMMUNICATIONS | 8:14373 | DOI: 10.1038/ncomms14373 | www.nature.com/naturecommunications
