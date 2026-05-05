# 02-machine-learning-in-compiler-optimization

PROCEEDINGS OF IEEE                                                                                                                            1




                              Machine Learning in Compilers
                                                     Zheng Wang and Michael O’Boyle



   Abstract—In the last decade, machine learning based com-                    hope of improving performance but could in some instances
pilation has moved from an an obscure research niche to                        damage it.
a mainstream activity. In this article, we describe the rela-                     Machine learning predicts an outcome for a new data point
tionship between machine learning and compiler optimisation
and introduce the main concepts of features, models, training                  based on prior data. In its simplest guise it can be considered
and deployment. We then provide a comprehensive survey and                     a from of interpolation. This ability to predict based on prior
provide a road map for the wide variety of different research                  information can be used to find the data point with the best
areas. We conclude with a discussion on open issues in the                     outcome and is closely tied to the area of optimisation. It is at
area and potential research directions. This paper provides both               this overlap of looking at code improvement as an optimisation
an accessible introduction to the fast moving area of machine
learning based compilation and a detailed bibliography of its                  problem and machine learning as a predictor of the optima
main achievements.                                                             where we find machine-learning compilation.
                                                                                  Optimisation as an area, machine-learning based or other-
   Index Terms—Compiler, Machine Learning, Code Optimisa-
tion, Program Tuning                                                           wise, has been studied since the 1800s [8], [9]. An interesting
                                                                               question is therefore why has has the convergence of these
                                                                               two areas taken so long? There are two fundamental reasons.
                          I. I NTRODUCTION                                     Firstly, despite the year-on year increasing potential perfor-
   “Why would anyone want to use machine learning to build a                   mance of hardware, software is increasingly unable to realise it
compiler?” It’s a view expressed by many colleagues over the                   leading to a software-gap. This gap has yawned right open with
last decade. Compilers translate programming languages writ-                   the advent of multi-cores (see also Section VI-B). Compiler
ten by humans into binary executable by computer hardware.                     writers are looking for new ways to bridge this gap.
It is serious subject studied since the 50s [1], [2], [3] where                   Secondly, computer architecture evolves so quickly, that it
correctness is critical and caution is a by-word. Machine-                     is difficult to keep up. Each generation has new quirks and
learning on the other hand is an area of artificial intelligence               compiler writers are always trying to play catch-up. Machine
aimed at detecting and predicting patterns. It is a dynamic                    learning has the desirable property of being automatic. Rather
field looking at subject as diverse as galaxy classification [4] to            than relying on expert compiler writers to develop clever
predicting elections based on tweeter feeds [5]. When an open-                 heuristics to optimise the code, we can let the machine learn
source machine learning compiler was announced by IBM in                       how to optimise a compiler to make the machine run faster,
2009 [6], some wry slashdots commentators picked up on the                     an approach sometimes referred to as auto-tuning [10], [11].
AI aspect, predicting the start of sentient computers, global net                 Machine learning is part of a tradition in computer science
and the war with machines from the Terminator film series.                     and compilation in increasing automation The 50s to 70s were
   In fact as we will see in this article, compilers and machine               spent trying to automate compiler translation, e.g. lex for
learning are a natural fit and have developed into an established              lexical analysis [12] and yacc for parsing [13], the last decade
research domain.                                                               by contrast has focussed on trying to automating compiler
                                                                               optimisation. As we will see it is not “magic” or a panacea for
A. It’s all about optimsiation                                                 compiler writers, rather it is another tool allowing automation
                                                                               of tedious aspects of compilation providing new opportunities
   Compiler have two jobs – translation and optimisation.
                                                                               for innovation. It also brings compilation nearer to the stan-
They must first translate programs into binary correctly.
                                                                               dards of evidence based science. It introduces an experimental
Secondly they have to find the most efficient translation
                                                                               methodology where we separate out evaluation from design
possible. There are many different correct translations whose
                                                                               and considers the robustness of solutions. Machine learning
performance varies significantly. The vast majority of research
                                                                               based schemes in general have the problem of relying on
and engineering practices is focussed on this second goal of
                                                                               black-boxes whose working we do not understand and hence
performance, traditionally misnamed optimisation. The goal
                                                                               trust. This problem is just as true for machine learning based
was misnamed because in most cases, till recently finding
                                                                               compilers. In this paper we aim to demystify machine learning
an optimal translation was dismissed as being too hard to
                                                                               based compilation and show it is a trustworthy and exciting
find and an unrealistic endeavour1 . Instead it focussed on
                                                                               direction for compiler research.
developing compiler heuristics to transform the code in the
                                                                                  The remainder of this article is structured as follows. We
   Z. Wang is with MetaLab, School of Computing and Communications,            first give an intuitive overview for machine learning in compil-
Lancaster University, U. K. E-mail: z.wang@lancaster.ac.uk                     ers in Section II. We then describe how machine learning can
   M. O’Boyle is with School of Informatics, University of Edinburgh, U. K.    be used to search for or to directly predict good compiler opti-
E-mail: mob@inf.ed.ac.uk
   1 In fact the term superoptimiser [7] was coined to describe systems that   misations in Section III. This is followed by a comprehensive
tried to find the optimum                                                      discussion in Section IV for a wide range of machine learning

PROCEEDINGS OF IEEE                                                                                                                                        2




                                                                Features of training
                                                                                                                       Features for new program




                                                                     programs
                       #inst.
                                                                                          Supervised
       for(…) {        #load                              ...
                                                                                           Machine        Model                       Model
         ...           #branch           Training                                          Learner                   New
       }                                 programs                                                                    program                      Prediction
                       cache miss rate                     +
                                                          ...
                                                    Optimal options



      (a) Feature engineering                              (b) Learning a model                                                (c) Deployment
Fig. 1: A generic view of supervised machine learning in compilers. In the feature engineering stage (a), the compiler developer
investigates data structures that are important to the problem. The data structures will typically be summarised as feature vectors.
In the learning stage (b), representative training programs are used to generate training examples. Each example consists of
feature vectors and the optimal compiler decision for each program. These training examples are fed into a machine learning
algorithm to automatically learn a model. In the deployment stage (c), the learned model is inserted into the compiler to predict
the best compiler decisions for new programs.

models that have been employed in prior work. Next, in                                 the vector can be an integer, real or Boolean value. The
Section V, we review how previous work chooses quantifiable                            process of feature selection and tuning is referred as feature
properties, or features, to represent programs. We discuss the                         engineering. This process may need to iteratively perform
challenges and limitations for applying machine learning to                            multiple times to find a set of high-quality features to build a
compilation, as well as open research directions in Section VII                        accurate machine learning model. In Section V, we provide a
before we summarise and conclude in Section VIII.                                      comprehensive review of feature engineering for the topic of
                                                                                       program optimisation.
  II. OVERVIEW OF M ACHINE L EARNING IN C OMPILERS
   Given a program, compiler writers would like to know what                           B. Learning a model
compiler heuristic or optimisation to apply in order to make
                                                                                          The second step is to use training data to derive a model us-
the code better. Better often means execute faster, but can
                                                                                       ing a learning algorithm. This process is depicted in Figure 1b.
also mean smaller code footprint or reduced power. Machine
                                                                                       Unlike other applications of machine learning, we typically
learning can be used to build a model used within the compiler,
                                                                                       generate our own training data. The compiler developer will
that makes such decisions for any given program.
   There are two main stages involved: learning and deploy-                            select training programs which are typical of the application
ment. The first stage learns the model based on training data,                         domain. For each training program, we calculate the feature
while the second uses the model on new unseen programs.                                values, compiling the program with different optimisation
Within the learning stage, we needs a way of representing                              options, and running and timing the compiled binaries to
programs in a systematic way. This representation is known                             discover the best-performing option. This process produces,
as the program features [14].                                                          for each training program, a training instance that consists
   Figure 1 gives a intuitive view how machine learning can                            of the feature values and the optimal compiler option for the
be applied to compilers. This process which includes feature                           program.
engineering, learning a model and deployment is described in                              The compiler developer then feeds these examples to a
the following sub-sections.                                                            machine learning algorithm to automatically build a model.
                                                                                       The learning algorithms job is to find from the training
A. Feature engineering                                                                 examples a correlation between the feature values and the
                                                                                       optimal optimisation decision. The learned model can then
   Before we can learn anything useful about programs, we
                                                                                       be used to predict, for a new set of features, what the optimal
first need to be able to characterise them. Machine learn-
                                                                                       optimisation option should be.
ing relies on a set of quantifiable properties, or features,
                                                                                          Because the performance of the learned model strongly
to characterise the programs (Figure 1a). There are many
                                                                                       depends on how well the features and training programs are
different features that can be used. These include the static
                                                                                       chosen, so that the processes of featuring engineering and
data structures extracted from the program source code or
                                                                                       training data generation often need to repeat multiple times.
the compiler intermediate representation (such as the number
of instructions or branches), dynamic profiling information
(such as performance counter values) obtained through runtime                          C. Deployment
profiling, or a combination of the both.                                                 In the final step, the learned model is inserted into the
   Standard machine learning algorithms typically work on                              compiler to predict the best optimisation decisions for new
fixed length inputs, so the selected prosperities will be sum-                         programs. This is demonstrated in Figure 1c. To make a
marised into a fixed length feature vector. Each element of                            prediction, the compiler first extracts the features of the input

PROCEEDINGS OF IEEE                                                                                                                                                                                 3



                                                                                                               TABLE I: Candidate code features used in [15].
1       k e r n e l void s q u a r e ( g l o b a l f l o a t ∗ in , g l o b a l f l o a t ∗ out ) {
2               int gid = get global id (0) ;
                                                                                                        Feature Desc.                              Feature Desc.
3               out [ gid ] = in [ gid ] ∗ in [ gid ] ;
4       }                                                                                               # Basic Blocks                             # Branches
                                                                                                        # Divergent Instr.                         # Instrs. in Divergent Regions
                                                                                                        (# instr. in Divergent regions)/(# total   # Divergent regions
                                 (a) Original OpenCL kernel                                             instr.)
                                                                                                        # Instrs                                   # Floating point instr.
                                                                                                        Avg. ILP per basic block                   (# integer instr.) / (# floating point instr.)
    1    k e r n e l void s q u a r e ( g l o b a l f l o a t ∗ in , g l o b a l f l o a t ∗ out ) {    # integer instr.                           # Math built-in func.
    2            int gid = get global id (0) ;                                                          Avg. MLP per basic block                   # loads
    3            i n t t i d 0 = 2∗ g i d + 0 ;                                                         # stores                                   # loads that are independent of the
    4            i n t t i d 1 = 2∗ g i d + 1 ;                                                                                                    coarsening direction
    5            out [ t i d 0 ] = in [ tid0 ] ∗ in [ tid0 ] ;                                          # barriers
    6            out [ t i d 1 ] = in [ tid1 ] ∗ in [ tid1 ] ;
    7    }


                 (b) Code transformation with a coarsening factor of 2                                 heuristics across GPU architectures [15]. Their approach con-
                                                                                                       siders six coarsening factors, (1, 2, 4, 8, 16, 32). The goal is to
Fig. 2: An OpenCL thread coarsening example reproduced
                                                                                                       develop a machine learning based model to decide whether
from [15]. The original OpenCL code is shown at (a) where
                                                                                                       an OpenCL kernel should be coarsened on a specific GPU
each thread takes the square of one element of the input array.
                                                                                                       architecture and if so what is the best coarsening factor.
When coarsened by a factor of two (b), each thread now
                                                                                                       Among many machine learning algorithms, they chose to use
processes two elements of the input array.
                                                                                                       an artificial neural network to model2 the problem. Construing
                                                                                                       such a model follows the classical 3-step supervised learning
                                                                                                       process, described as follows.
program, and then feeds the extracted feature values to the
                                                                                                            a) Feature engineering: To describe the input OpenCL
learned model to make a prediction.
                                                                                                       kernel, Magni et al. use static code features extracted from
   The advantage of the machine learning based approach is                                             the compiler’s intermediate representation. Specifically, they
that the entire process of building the model can be easily                                            developed a compiler-based tool to obtain the feature values
repeated whenever the compiler needs to target a new hardware                                          from the program’s LLVM bitcode [19]. They started from
architecture, operating system or application domain. The                                              17 candidate features. These include things like the number
model built is entirely derived from experimental results and                                          of and types of instructions and memory level parallelism
is hence evidence based.                                                                               (MLP) within an OpenCL kernel. Table I gives the list of
                                                                                                       candidate features used in [15]. Typically, candidate features
                                                                                                       can be chosen based on developers’ intuitions, suggestions
D. Example
                                                                                                       from prior works, or a combination of both. After choosing
   As an example to illustrate these steps, consider thread                                            the candidate features, a statistical method called Principal
coarsening [16] for GPU programs. This code transformation                                             Component Analysis (see also Section IV-B) is applied to
technique works by giving multiple work-items (or work                                                 map the 17 candidate features into 7 aggregated features,
elements) to one single thread. It is similar to loop unrolling,                                       so that each aggregated feature is a linear combination of
but applied across parallel work-items rather than across serial                                       the original features. This technique is known as “feature
loop iterations.                                                                                       dimension reduction” which is discussed at Section V-D2.
   Figure 2 (a) shows a simple OpenCL kernel where a thread                                            Dimension reduction helps eliminating redundant information
operates on a work-item of the one-dimensional input array,                                            among candidate features, allowing the learning algorithm to
in, at a time. The work-item to be operated on is specified                                            perform more effectively.
by the value returned from the OpenCL get_global_id()                                                       b) Learning the model: For the work presented in [15],
API. Figure 2 (b) shows the transformed code after applying                                            16 OpenCL benchmarks were used to generate training data.
a thread coarsen factor of two, where each thread processes                                            To find out which of the six coarsening factors performs best
two elements of the input array.                                                                       for a given OpenCL kernel on a specific GPU architecture,
   Thread coarsening can improve performance through in-                                               we can apply each of the six factors to an OpenCL kernel and
creasing instruction-level parallelism [17], reducing the num-                                         records its execution time. Since the optimal thread-coarsening
ber of memory-access operations [18], and eliminating redun-                                           factor varies across hardware architectures, this process needs
dant computation when the same value is computed in every                                              to repeat for each target architecture. In addition to finding the
work-item. However, it can also have several negative side-                                            best-performing coarsening factor, Magni et al. also extracted
effects such as reducing the total amount of parallelism and                                           the aggregated feature values for each kernel. Applying these
increasing the register pressure, which can lead to slowdown                                           two steps on the training benchmarks results in a training
performance. Determining when and how to apply thread                                                  dataset where each training example is composed of the opti-
coarsening is non-trivial, because the best coarsening factor                                          mal coarsening factor and feature values for a training kernel.
depends on the target program and the hardware architecture                                            The training examples are then fed into a learning algorithm
that the program runs on [17], [15].                                                                      2 In fact, Magni et al. employed a hieratical approach consisting of multiple
   Magni et al. show that machine learning techniques can                                              artificial neural networks [15]. However, these networks are trained using the
be used to automatically construct effective thread-coarsening                                         same process.

PROCEEDINGS OF IEEE                                                                                                                                   4



                                                                                 of a potential compiler decision, without relying on extensive
             Compiler                             Yes
               Compiler
                                  Continue?           Yes Cost function                 profiling. The second strategy is to directly predict the best-
             heuristic               Continue?                Cost function
input          heuristic                   evaluate an option           quality metric performing option.
program
   input                               No     evaluate an option            quality metric
   program                                 No
          available options         best-found option
             available options         best-found option
               (a) Use a cost function to guide compiler decisions               A. Building a cost function

              Feature                      Predictive                               Many compiler heuristics rely on a cost function to es-
                                                           predicted option
                 Feature
             extraction                       Predictive
                                             model            predicted option   timate the quality of a compiler option. Depending on the
input           extraction                      model                            optimisation goal, the quality metric can be execution time, the
program
   input                     features
   program                      features                                         code size, or energy consumption etc. Using a cost function, a
                (b) Use a model to directly predict the decision                 compiler can evaluate a range of possible options to choose the
                                                                                 best one, without needing to compile and profile the program
Fig. 3: There are in general two approaches to determine the
                                                                                 with each option.
optimal compiler decision using machine learning. The first
                                                                                    1) The problem of hand-crafted heuristics: Traditionally,
one is to learn a cost or priority function to be used as a proxy
                                                                                 a compiler cost function is manually crafted. For example, a
to select the best-performing option (a). The second one is to
                                                                                 heuristic of function inlining adds up a number of relevant
learn a predictive model to directly predict the best option.
                                                                                 metrics, such as the number of instructions of the target
                                                                                 function to be inlined, the callee and stack size after inlining,
which tries to find a set of model parameters (or weights) so                    and compare the resulted value against a pre-defined threshold
that overall prediction error on the training examples can be                    to determine if it is profitable to inline a function [25]. Here,
minimised. The output of the learning algorithm is an artificial                 the importance or weights for metrics and the threshold are
neural network model where its weights are determined from                       determined by compiler developers based on their experience
the training data.                                                               or via “trail-and-error”. Because the efforts involved in tuning
                                                                                 the cost function is so expensive, many compilers simply use
     c) Deployment: The learned model can then be used
                                                                                 “one-size-fits-all” cost function for inlining. However, such a
to predict the optimal coarsening factor for unseen OpenCL
                                                                                 strategy is ineffective. For examples, Cooper et al. show that
programs. To do so, static source code features are first
                                                                                 a “one-size-fits-all” strategy for inlining often delivers poor
extracted from the target OpenCL kernel; the extracted feature
                                                                                 performance [26]; other studies also show that that the optimal
values are then fed into the model which decides whether
                                                                                 thresholds to use to determine when to inline changes from
to coarsen or not and which coarsening factor should use.
                                                                                 one program to the other [27], [28].
The technique proposed in [15] achieves an average speedup
between 1.11x and 1.33x across four GPU architectures and                           Hand-crafted cost functions are widely used in compilers.
does not lead to degraded performance on a single benchmark.                     Other examples include the work conducted by Wagner et
                                                                                 al. [29] and Tiwari et al. [30]. The former combines a Markov
                                                                                 model and a human-derived heuristic to statically estimate the
                             III. M ETHODOLOGY                                   execution frequency of code regions (such as function innova-
   One of the key challenges for compilation is to select                        tion counts). The later calculates the energy consumption of an
the right code transformation, or sequence of transformations                    applicaiton by assigning a weight to each instruction type. The
for a given program. This requires effectively evaluating the                    efficiency of these approaches highly depend on the accuracy
quality of a possible compilation option e.g. how will a code                    of the estimations given by the manually tuned heuristic.
transformation affect eventual performance.                                         The problem of relying on a hand-tuned heuristic is that
   A naive approach is to exhaustively apply each legal                          the cost and benefit of a compiler optimisation often depends
transformation option and then profile the program to collect                    on the underlying hardware; while hand-crafted cost functions
the relevant performance metric. Given that many compiler                        could be effective, manually developing one can take months
problems have a massive number of options, exhaustive search                     or years on a single architecture. This means that tuning the
and profiling is infeasible, prohibiting the use of this approach                compiler for each new released processor is hard and is often
at scale. This search based approach to compiler optimisation                    infeasible due to the drastic efforts involved. Because cost
is known as iterative compilation [20], [21] or auto-tuning                      functions are important and manually tuning a good function
[10], [22]. Many techniques have been proposed to reduce the                     is difficult for each individual architecture, researchers have
cost of searching a large space [23], [24]. In certain cases, the                investigated ways to use machine learning to automate this
overhead is justifiable if the program in question is to be used                 process.
many times e.g. in a deeply embedded device. However, its                           In the next subsection, we review a range of previous
main limitation remains: it only finds a good optimisation for                   studies on using machine learning to tune cost functions for
one program and does not generalise into a compiler heuristic.                   performance and energy consumption – many of which can be
   There are two main approaches for solving the problem of                      applied to other optimisation targets such as the code size [31]
scalably selecting compiler options that work across programs.                   or a trade-off between energy and runtime.
A high level comparison of both approaches is given in                              2) Cost functions for performance: The Meta Optimization
Figure 3. The first strategy attempts to develop a cost (or                      framework [32] uses genetic programming (GP) to search for
priority) function to be used as a proxy to estimate the quality                 a cost function, y ← f (x), which takes in a feature vector,

PROCEEDINGS OF IEEE                                                                                                                               5




                    //
                +        4.0                                                                                     Keep well-
            +            4.0               Generate inital    Evaluate                                    Yes        Keep well- Create new functions
                                                                                                                                                Randomize t
                                                                                            Continue?            performing
      #inst.        x                            Generate inital
                                           cost functions     functions                  Evaluate                               using remaining ones
                                                                                                                                           expressions to c
  #inst.            x                                                                                                performing
                                                                                                                  functions
        #branches         #loads                   cost functions                       functions
                                                                                                No
                                                                                                                                                new function
                                                                                                                       functions
                                                                                               Exit
    #branches                  #loads
 (a) An example cost function in [32]                                     (b) A simple view of the generic programming technique in [32]

Fig. 4: A simple view of the genetic programming (GP) approach presented at [32] for tuning compiler cost functions. Each
candidate cost function is represented as an expression tree (a). The workflow of the GP algorithm is presented at (b).


x, and produces a real-valued priority, y. Figure 4 depicts                        hardware architecture design. As power or energy readings
the workflow of the framework. This approach is evaluated                          are continuous real values, most of the prior work on power
on a number of compiler problems, including hyperblock                             modelling use regression-based approaches.
formation3 , register allocation, and data prefetching, showing                       Linear regression is a widely used technique for energy
that machine learned cost functions outperform human-crafted                       modeling. Benini et al. developed a linear regression-based
ones. A similar approach is employed by Cavazos et al. find                        model to estimate power consumption at the instruction lev-
cost functions for performance and compilation overhead for                        el [46]. The framework presented by Rethinagiri et al.. [47]
a Java just-in-time compiler [33]. The COLE compiler [34]                          uses parameterised formulas to estimate power consumption
uses a variance of the GP algorithm called Strength Pareto                         of embedded systems. The parameters of the formulas are
Evolutionary Algorithm2 (SPEA2) [35] to learn cost functions                       determined by applying a regression-based algorithm to refer-
to balance multiple objectives (such as program runtime,                           ence data obtained with hand-crafted assembly code and power
compilation overhead and code size). In Section IV-C, we                           measurements. In a more recent work, Schürmans et al. also
describe the working mechanism of GP-like search algorithms.                       adopt a regression-based method for power modelling [48],
    Another approach to tune the cost functions is to predict the                  but the weights of the regression model are determined using
execution time or speedup of the target program. The Qilin                         standard benchmarks instead of hand-written assembly pro-
compiler [36] follows such an approach. It uses curve fitting                      grams.
algorithms to estimate the runtime for executing the target                           Other works employ the artificial neural network (ANN)
program of a given input size on the CPU and the GPU. The                          to automatically construct power models. Curtis-Maury et al.
compiler then uses this information to determine the optimal                       develop an ANN-based model to predict the power consump-
loop iteration partition across the CPU and the GPU. The Qilin                     tion of OpenMP programs on multi-core systems [49]. The
compiler relies on an application-specific function which is                       inputs to the model are hardware performance counter values
built on a per program base using reference inputs. The curve                      such as the cache miss rate, and the output is the estimated
fitting (or regression – see also Section IV) model employed by                    power consumption. Su et al. adopt a similar approach by
the Qilin compiler can model with continuous values, making                        developing an ANN predictor to estimate the runtime and
it suitable for estimating runtime and speedup. In [37], this                      power consumption for mapping OpenMP programs on Non-
approach is extended, which developed a relative predictor that                    Uniform Memory Access (NUMA) multi-cores. This approach
predicts whether an unseen predictor will improve significantly                    is also based on runtime profiling of the target program, but it
on a GPU relative to a CPU. This is used for runtime                               explicitly considers NUMA-specific information like local and
scheduling of OpenCL jobs.                                                         remote memory accesses per cycle.
    The early work conduced by Brewer proposed a regression-
based model to predict the execution of a data layout scheme                       B. Directly predict the best option
for parallelization, by considering three parameters [38]. Using
                                                                                      While a cost function is useful for evaluating the quality
the model, their approach can select the optimal layout for over
                                                                                   of compiler options, the overhead involved in searching for
99% of the time for a Partial Differential Equations (PDE)
                                                                                   the optimal option may still be prohibitive. For this reason,
solver across four evaluation platforms. Other previous works
                                                                                   researchers have investigated ways to directly predict the best
also use curve fitting algorithms to build a cost function to
                                                                                   compiler decision using machine learning for relatively small
estimate the speedup or runtime of sequential [39], [40], [41],
                                                                                   compilation problems.
OpenMP [42], [43], [44], and more recently for deep learning
                                                                                      Monsifrot et al. pioneered the use of machine learning
applications [45].
                                                                                   to predict the optimal compiler decision [14]. This work
    3) Cost functions for energy consumption: In addition to
                                                                                   developed a decision tree based approach to determine whether
performance, there is an extensive body of work investigates
                                                                                   it is beneficial to unroll a loop based on information such as
ways to build energy models for software optimisation and
                                                                                   the number of statements and arithmetic operations of the loop.
   3 Hyperblock formation combines basic blocks from multiple control paths        Their approach makes a binary decision on whether to unroll
to form a predicated, larger code block to expose instruction level parallelism.   a loop but not how many times the loop should be unrolled.

PROCEEDINGS OF IEEE                                                                                                                     6



Later, Stephenson and Amarasinghe advanced [14] by directly
predicting the loop unroll factor [50] by considering eight
unroll factors, (1, 2, . . . , 8). They formulated the problem as a
multi-class classification problem (i.e. each loop unroll factor
is a class). They used over 2,500 loops from 72 benchmarks
to train two machine learning models (a nearest neighbor and
a support vector machines model) to predict the loop unroll




                                                                          Y
factor for unseen loops. Using a richer set of features than [14],                                f(x)       y
their techniques correctly predict the unroll factor for 65% of
the testing loops, leading to on average, a 5% improvement
for the SPEC 2000 benchmark suite.
   For sequential programs, there is extensive work in pre-
dicting the best compiler flags [51], [52], code transformation
options [53], or tile size for loops [54], [55]. This level of                                           X
interest is possibly due to the restricted nature of the problem,
allowing easy experimentation and comparision against prior
                                                                      Fig. 5: A simple regression-based curve-fitting example. There
work.
                                                                      are five training examples in this case. A function, f , is trained
   Directly predicting the optimal option for parallel programs
                                                                      with the training data, which maps the input x to the output
is harder than doing it for sequential programs, due to the
                                                                      y. The trained function can predict the output of an unseen x.
complex interactions between the parallel programs and the
underlying parallel architectures. Nonetheless, there are works
on predicting the optimal number of threads to use to run an            There are also techniques that sit at the boundary of
OpenMP program [44], [56], the best parameters to used to             supervised and unsupervised learning. These techniques refine
compile a CUDA programs for a given input [57] the thread             the knowledge gathered during offline learning or previous
coarsening parameters for OpenCL programs for GPUs [15].              runs using empirical observations obtained during deployment.
These papers show that supervised machine learning can be a           We review such techniques in Section IV-C. This sections
powerful tool for modelling problems with a relatively small          concludes with a discussion of the relative merits of different
number of optimisation options.                                       modelling approaches for compiler optimisation.
              IV. M ACHINE L EARNING M ODELS
   In this section, we review the wide range of machine               A. Supervised learning
learning models used for compiler optimisation.                          1) Regression: A widely used supervised learning tech-
   There are two major subdivisions of machine learning               nique is called regression. This technique has been used in
techniques that have previously been used in compiler opti-           various tasks, such as predicting the program execution time
misations: supervised and unsupervised learning. Using su-            input [36] or speedup [37] for a given input, or estimating the
pervised machine learning, a predictive model is trained on           tail latency for parallel workloads [59].
empirical performance data (labelled outputs) and important              Regression is essentially curve-fitting. As an example, con-
quantifiable properties (features) of representative programs.        sider Figure 5 where a regression model is learned from five
The model learns the correlation between these feature values         data points. The model takes in a program input size, X,
and the optimisation decision that delivers the optimal (or           and predicts the execution time of the program, Y . Adhering
nearly optimal) performance. The learned correlations are used        to supervised learning nomenclature, the set of five known
to predict the best optimisation decisions for new programs.          data points is the training data set and each of the five points
Depending on the nature of the outputs, the predictive model          that comprise the training data is called a training example.
can be either a regression model for continuous outputs or a          Each training example, (xi , yi ), is defined by a feature vector
classification model for discrete outputs.                            (i.e. the input size in our case), xi , and a desired output (i.e.
   In the other subdivision of machine learning, termed unsu-         the program execution time in our case), yi . Learning in this
pervised learning, the input to the learning algorithm is a set       context is understood as discovering the relation between the
of input values merely – there is no labelled output. One form        inputs (xi ) and the outputs (yi ) so that the predictive model
of unsupervised learning is clustering which groups the input         can be used to make predictions for any new, unseen input
data items into several subsets. For example, SimPoint [58], a        features in the problem domain. Once the function, f , is in
simulation technique, uses clustering to pick represent program       place, one can use it to make a prediction by taking in a new
execution points for program simulation. It does so by first          input feature vector, x. The prediction, y, is the value of the
dividing a set of program runtime information into groups             curve that the new input feature vector, x, corresponds to.
(or clusters), such that points within each cluster are similar          There are a range of machine learning techniques can be
to each other in terms of program structures (loops, memory           used for regression. These include the simple linear regression
usages etc.); it then chooses a few points of each cluster to         model and more advanced models like support vector ma-
represent all the simulation points within that group without         chines (SVMs) and artificial neural networks (ANNs). Linear
losing much information.                                              regression is effective when the input (i.e. feature vectors) and

PROCEEDINGS OF IEEE                                                                                                                                                                    7




                                                                                                                                          Random Forests
    TABLE II: Regression techniques used in prior works.
 Modelling Technique                  Application                                  References                                    Tree 1        y1
                                                                                                                                                               yout = ∑wi yi
                                                                                                                                          y2
                                                                                                                           ...
                                                                                                                                 Tree 2             Ensemble                   Prediction
 Linear Regression                    Exec. Time Estimation                        [60], [36], [41]
 Linear Regression                    Perf. & Power Prediction                     [61], [62], [63]
 Artificial Neural Networks           Exec. Time Estimation                        [60], [44], [37]

                                                                                                                                               yn
                                                                                                        feature                  Tree n
                             Yes     F1 (Commun. - Computation Ratio) < 0.03            No              vector x
                                                                   F3 (% Local Mem Access Avg. #Work-
              F4 (Computation – Mem Ratio) < 7.65                         items per Kernel) < 3300      Fig. 7: Random forests are an ensemble learning algorithm.
                                   F3 < 21              F3 < 0.02            CPU             GPU
                                                                                                        It aggregates the outputs of multiple decision trees to form a
                                                                                                        final prediction. The idea is to combine the predictions from
 F2 ( % Coalesced Mem Access) < 0.99     GPU      F4 < 134          GPU                                 multiple individual models together to make a more robust,
                                             F4 < 30
                       CPU         GPU                       GPU
                                                                                                        accurate prediction than any individual model.

                                      GPU              CPU


Fig. 6: A decision tree for determining which device (CPU                                               determining the loop unroll factor [14], [68], deciding the prof-
or GPU) to use to run an OpenCL program. This diagram is                                                itability of using GPU acceleration [66], [69], and selecting the
reproduced from [66].                                                                                   optimal algorithm implementation [70]. The advantage of a
                                                                                                        decision tree is that the learned model is interpretable and can
                                                                                                        be easily visualised. This enables users to understand why a
output (i.e. labels) have a strong linear relation. SVM and ANNs                                        particular decision is made by following the path from the root
can model both linear and non-linear relations, but typically                                           node to a leaf decision node. For example, Figure 6 depicts the
require more training examples to learn an effective model                                              decision tree model developed in [66] for selecting the best-
when compared with simple linear regression models.                                                     performing device (CPU or GPU) to run an OpenCL program.
   Table II gives some examples of regression techniques that                                           To make a prediction, we start from the root of the tree; we
have been used in prior work for code optimisation and the                                              compare a feature value (e.g. the communication-computation
problem to be modelled.                                                                                 ratio) of the target program against a threshold to determine
   2) Classification: Supervised classification is another tech-                                        which branch of the tree to follow; and we repeat this process
nique that has been widely used in prior work of machine                                                until we reach a leaf node where a decision will be made.
learning based code optimisation. This technique takes in a                                             It is to note that the structure and thresholds of the tree are
feature vector and predicts which of a set of classes the feature                                       automatically determined by the machine learning algorithm,
vector is associated with. For example, classification can be                                           which may change when we target a different architecture or
used to predict which of a set of unroll factors should be used                                         application domain.
for a given loop, by taking in a feature vector that describes                                             Decision trees make the assumption that the feature space
the characteristics of the target loop (see also Section II-D).                                         is convex i.e. it can be divided up using hyperplanes into
   The k-nearest neighbour (KNN) algorithm is a simple yet                                              different regions each of which belongs to a different category.
effective classification technique. It finds the k closet training                                      This restriction is often appropriate in practice. However, a
examples to the input instance (or program) on the feature                                              significant drawback of using a single decision tree is that
space. The closeness (or distance) is often evaluated using the                                         the model can over-fit due to outliers in the training data
Euclidean distance, but other metrics can also be used. This                                            (see also Section IV-D). Random forests [71] have therefore
technique has been used to predict the optimal optimisation                                             been proposed to alleviate the problem of over fitting. Random
parameters in prior works [50], [64], [65]. It works by first                                           forests are an ensemble learning method [72]. As illustrated
predicting which of the training programs are closet (i.e. near-                                        in Figure 7, it works by constructing multiple decision trees
est neighbours) to the incoming program on the feature space;                                           at training time. The prediction of each tree depends on the
it then uses the optimal parameters (which are found during                                             values of a random vector sampled independently on the
training time) of the nearest neighbours as the prediction                                              feature value. In this way, each tree is randomly forced to be
output. While it is effective on small problems, KNN also has                                           insensitive to some feature dimensions. To make a prediction,
two main drawbacks. Firstly, it must compute the distance                                               random forests then aggregate the outcomes of individual
between the input and all training data at each prediction. This                                        trees to form an overall prediction. It has been employed to
can be slow if there is a large number of training programs                                             determine whether to inline a function or not [73], delivering
to be considered. Secondly, the algorithm itself does not learn                                         better performance than a single-model-based approach. We
from the training data; instead, it simply selects the k nearest                                        want to highlight that random forests can also be used for re-
neighbours. This means that the algorithm is not robust to                                              gression tasks. For instances, it has been used to model energy
noisy training data and could choose an ill-suited training                                             consumption of OpenMP [74] and CUDA [75] programs.
program as the prediction.                                                                                 Logical regression is a variation of linear regression but
   As an alternative, the decision tree has been used in prior                                          is often used for classification. It takes in the feature vector
works for a range of optimisation problems. These include                                               and calculates the probability of some outcome. For example,
choosing the parallel strategy for loop parallelisation [67],                                           Cavazos and O’Boyle used logical regression to determine

PROCEEDINGS OF IEEE                                                                                                                                                  8



                                               kernel void square ( global float* in , global float* out ){
                                                 int gid = get_global_id (0) ;
                                                 out [ gid ] = in [ gid ] * in [ gid ];
                                                  ...
                                               }

                 Source Code



   (a)       Processing Layer

                                                                                                          Outputs of DNN 1

   (b)                DNN 1                   AMD HD 5900
                                            AMD Tahiti 7970
                                            NVIDIA GTX 480
                                           NVIDIA Tesla K20c




   (c)                DNN 2

                                                                                                              Output of DNN 2

   (d)           Output Layer                                         AMD HD 5900
                                                                    AMD Tahiti 7970
                                                                    NVIDIA GTX 480
                                                                   NVIDIA Tesla K20c




                                                                        AMD HD 5900                  AMD Tahiti 7970            NVIDIA GTX 480   NVIDIA Tesla K20c
                                                                           CF: 2                         CF: 2                      CF: 4             CF: 1


Fig. 8: A simplified view of the internal state for the DeepTune DNN framework [76] when it predicts the optimal OpenCL
thread coarsening factor. Here a DNN is learned for each of the four target GPU architectures. The activations in each layer
of the four models increasingly diverge (or specialise) towards the lower layers of the model. It is to note that some of the
DeepTune layers are omitted to aid presentation.


the optimisation level of Jike RVM. Like decision trees,                                  tionship between the input and the output (i.e. the prediction).
logical regression also assumes that the feature values and                               As an example, consider Figure 8 that visualizes the internal
the prediction has a linear relation.                                                     state of DeepTune [76] when predicting the optimal thread
   More advanced models such as SVM classification has been                               coarsening factor for an OpenCL kernel (see Section II-D).
used for various compiler optimisation tasks [44], [77], [78].                            Figure 8 (a) shows the first 80 elements of the input source
SVMs use kernel functions to compute the similarity of feature                            code tokens as a heatmap in which each cell’s color reflects
vectors. The radial basis function (RBF) is commonly used in                              an integer value assigned to a specific token. Figure 8 (b)
prior works [44], [79] because it can model both linear and                               shows the neurons of the first DNN for each of the four GPU
non-linear problems. It works by mapping the input feature                                platforms, using a red-blue heatmap to visualize the intensity
vector to a higher dimensional space where it may be easier                               of each activation. If we have a close look at the heatmap,
to find a linear hyper-plane to well separate the labelled data                           we can find that a number of neurons in the layer with
(or classes).                                                                             different responses across platforms. This indicates that the
   Other machine learning techniques such as Kernel Canoni-                               DNN is partly specialised to the target platform. As information
cal Correlation Analysis and naive Bayes have also been used                              flows through the network (layers c and d in Figure 8), the
in prior works to predict stencil program configurations [80]                             layers become progressively more specialised to the specific
or detect parallel patterns [81].                                                         platform.
   3) Deep neural networks: In recent years, deep neural net-
works [82] have been shown to be a powerful tool for tackling                                One of the hurdles for applying DNNs to compiler opti-
a range of machine learning tasks like image recognition [83],                            misation is that DNNs typically require a large amount of
[84] and audio processing [85]. DNNs have recently used to                                examples to learn over; and unlike other domains such as
model program source code [86] for various software engineer-                             image recognitions and machine translations where there are
ing tasks (see also Section VI-C), but so far there is little work                        millions of labelled data readily available, compiler developers
of applying DNNs to compiler optimisation. A recent attempt                               typically only have access to a dozen of benchmarks and
in this direction is the DeepTune framework [76], which uses                              have to generate the training data themselves. The recent
DNNs to extract source code features (see also Section V-C).                              work conducted by Cummins et al. [87] shows that it is
   The advantage of DNNs is that it can compactly represent                               possible to learn from open source repositories like GitHub
a significantly larger set of functions than a shallow network,                           to automatically generate an unbound number of high-quality
where each function is specialised at processing part of the                              OpenCL benchmarks. If this technique can be applied to
input. This capability allows DNNs to model the complex rela-                             other programming languages and application domains and

PROCEEDINGS OF IEEE                                                                                                                               9



we can find ways to reduce the cost of generating program                                         Cluster-1    Cluster-2   Cluster-3
                                                                                            3
training data, we can then greatly extend the reach of DNNs
                                                                                            2
to compiler-based code optimisation.
                                                                                            1
B. Unsupervised learning                                                                    0
   Unlike supervised learning models which learn a correlation                             -1
from the input feature values to the corresponding outputs,
                                                                                           -2
unsupervised learning models only take it the input data (e.g.
the feature values). This technique is often used to model the                             -3
underlying structure of distribution of the data.
   Clustering is a classical unsupervised learning problem. The                              -4      -3       -2    -1     0      1    2   3
k-means clustering algorithm [88] groups the input data into                      Fig. 9: Using k-means to group data points into three clusters.
k clusters. For example, in Figure 9, a k-means algorithm is                      In this example, we group the data points into three clusters
used to group data points into three clusters on a 2-dimensional                  on a 2-d feature space.
feature space. The algorithm works by grouping data points
that are close to each other on the feature space into a cluster.                 the target problem. For instance, the SPIRAL auto-tuning
K-means is used to characterise program behaviour [58], [89].                     framework uses a stochastic evolutionary search algorithm to
It does so by clustering program execution into phase groups,                     choose a fast formula (or transformation) for signal processing
so that we can use a few samples of a group to represent the                      applications [99]. Li et al. use genetic algorithms to search for
entire program phases within a group. K-means is also used in                     the optimal configuration to determine which sorting algorithm
the work presented in [90] to summarise the code structures                       to use based on the unsorted data size [100]. The Petabricks
of parallel programs that benefit from similar optimisation                       compiler offers a more general solution by using evolutionary
strategies. In addition to k-means, Martins et al. employed                       algorithms to search for the best-performing configurations
the Fast Newman clustering algorithm [91] which works on                          for a set of algorithms specified by the programmer [101].
network structures to group functions that may benefit from                       In addition to code optimisation, EAs have also been used
similar compiler optimisations [92].                                              to create Pareto optimal program benchmarks under various
   Principal Component Analysis (PCA) is a statistical method                     criteria [102].
for unsupervised learning. This method has been heavily used                         As an example, consider how an EA can be employed in
in prior work to reduce the feature dimension [93], [23], [94],                   the context of iterative compilation to find the best compiler
[95], [15]. Doing so allows us to model a high-dimensional                        flags for a program [23], [34], [103]. Figure 10 depicts
feature space with a smaller number of representative variables                   how an EA can be used for this purpose. The algorithm
which, in combination, describe most of the variability found                     starts from several populations of randomly chosen compiler
in the original feature space. PCA is often used to discover                      flag settings. It compiles the program using each individual
the common pattern in the datasets in order to help clustering                    compiler flag sequence, and uses a fitness function to evaluate
exercises. It is used to select representative programs from a                    how well a compiler flag sequence performs. In our case, a
benchmark suite [93], [96]. In Section V-D, we discuss PCA                        fitness function can simply return the reciprocal of a program
in further details.                                                               runtime measurment, so that compiler settings that give faster
   Autoencoders are a recently proposed artificial neural net-                    execution time will have a higher fitness score. In the next
work architecture for discovering the efficient codings of input                  epoch, the EA algorithm generates the next populations of
data in an unsupervised fashion [97]. This technique can be                       compiler settings via mechanisms like reproduction (cross-
used in combination of a natural language model to first                          over) and mutation among compiler flag settings. This results
extract features from program source code and then find a                         in a new generation of compiler flag settings and the quality
compact representation of the source code features [98]. We                       of each setting will be evaluated again. In a mechanism
discuss autoencoders in Section V-D when reviewing feature                        analogous to natural selection, a certain number of poorly
dimensionality reduction techniques.                                              performing compiler flags within a population are chosen
                                                                                  to die in each generation. This process terminates when no
C. Online learning                                                                further improvement is observed or the maximum number of
  1) Evolutionary search: Evolutionary algorithms (EAs) or                        generations is reached, and the algorithm will return the best-
evolutionary computation like genetic algorithms, genetic pro-                    found program binary as a result.
gramming4 and stochastic based search have been employed                             Three are three key operations in a classical EA algrotihm:
to find a good optimisation solution from a large search                          selection, cross-over and mutation. The probability of an
space. An EA applies a principles inspired by biological                          optimisation option being selected for dying is often inversely
evolution to find an optimal or nearly optimal solution for                       proportional to its fitness score. In other words, options that
                                                                                  are relatively fitter (e.g. give faster program runtime) are more
   4 A genetic algorithm (GA) is represented as a list of actions and values,
                                                                                  likely to survive and remain a part of the population after
often a string, while a genetic program (GP) is represented as a tree structure
of actions and values. For example, GP is applied to the abstract syntax tree     selection. In cross-over, a certain number of offsprings are
of a program to search for useful features in [68].                               produced by mixing some existing optimisation options (e.g.

PROCEEDINGS OF IEEE                                                                                                                                        10



           Individual compiler flag setting             compiler setting population


                                                         ...
                                                                                                               Environment
                             ...            ...                        ...




                                                                                               action a(t+1)
    1st gen.
                                                                                                                                reward r(t)
         Selection                                                                                              Learning
                     ...                  ...                        ...                                        Algorithm
                           -o v e r
                      Cross                                            mutation
                                                                                                                                       state s(t)

                                                          ...
                                                                                       Fig. 11: The working mechanism of reinforcement learning
   2nd gen.                  ...                ...                        ...

                                          ...                                         combine supervised learning and evolutionary algorithms [23],

                              ...               ...       ...              ...
                                                                                      [104] – by first using an offline learned model to predict
(N-1)th gen.                                                                          the most promising areas of the design space (i.e. to narrow
                                                                                      down the search areas), and then searching over the predicted
                       ...                  ...                        ...            areas to refine the solutions. Moreover, instead of predicting
                                                                                      where in the search space to focus on, one can also first

                               ...                ...      ...               ...
                                                                                      prune the search space to reduce the number of options to
     Nth gen.                                                                         search over. For example, Jantz and Kulkarni show that the
                                                                                      search space of phase ordering5 can be greatly reduced if we
                                                                                      can first remove phases whose application order is irrelevant
                                      Best-performing                                 to the produced code [105]. Their techniques are claimed to
                                           Binary                                     prune the exhaustive phase order search space size by 89% on
Fig. 10: Use an evolutionary algorithm to perform iterative                           average.
compilation. The algorithm starts from several initial popula-                           2) Reinforcement learning: Another class of online learn-
tions of randomly chosen compiler flag sequences. It evaluates                        ing algorithms is reinforcement learning (RL) which is some-
the performance of individual sequences to remove poorly                              times called “learning from interactions”. The algorithm tries
performing sequences in each population. It then applies cross-                       to learn how to maximise the rewards (or performance) itself.
over and mutation to create a new generation of populations.                          In other words, the algorithm needs to learn, for a given input,
The algorithm returns the best-performing program binary                              what is the correct output or decision to take. This is different
when it terminates.                                                                   from supervised learning where the correct input/output pairs
                                                                                      are presented in the training data.
                                                                                         Figure 11 illustrates the working mechanism of RL. Here
compiler flags). The likelihood of an existing option being                           the learning algorithm interacts with its environment over a
chosen for cross-over is again proportional to its fitness. This                      discrete set of time steps. At each step, the algorithm evaluate
strategy ensures that good optimisations will be preserved over                       the current state of its environment, and executes an action.
generations, while poorly performing optimisations will grad-                         The action leads to a change in the state of the environment
ually die out. Finally, mutation randomly changes a preserved                         (which the algorithm can evaluate in the next time step), and
optimisation, e.g. by turning on/off an option or replacing a                         produces an immediate reward. For examples, in a multi-
threshold value in a compiler flag sequence. Mutation reduces                         tasking environment, a state could be the CPU contention and
the chance that the algorithm gets stuck with a locally optimal                       which processor cores are idle, an action could be where to
optimisation.                                                                         place a process, and a reward could be the overall system
   EAs are useful for exploring a large optimisation space                            throughput. The goal of RL is to maximize the long-term
where it is infeasible to just enumerate all possible solutions.                      cumulative reward by learning an optimal strategy to map
This is because an EA can often converge to the most promis-                          states to actions.
ing area in the optimisation space quicker than a general                                RL is particularly suitable for modelling problems that have
search heuristic. The EA is also shown to be faster than                              an evolving natural, such as dynamic task scheduling, where
a dynamic programming based search [22] in finding the                                the optimal outcome is achieved through a series of actions.
optimal transformation for the Fast Fourier Transformation                            RL has been used in prior resarch to schedule RAM memory
(FFT) [99]. When compared to supervised learning, EAs have                            traffics [106], selecting software component configurations at
the advantage of requiring little problem specific knowledge,                         runtime [107], and configure virtual machines [108]. An early
and hence that they can be applied on a broad range of                                work of using RL for program optimisation was conduced by
problems. However, because an EA typically relies on the                              Lagoudakis and Littman [109]. They use RL to find the cut-off
empirical evidences (e.g. running time) for fitness evaluation,                       point to switch between two sorting algorithms, quickSort
the search time can still be prohibitively expensive. This                            and insertionSort.
overhead can be reduced by using a machine learning based
cost model [41] to estimate the potential gain (e.g. speedup) of                        5 Compiler phase ordering determines at which order a set of compiler
a configuration (see also Section III-A). Another approach is to                      optimisation passes should be applied to a given program.

PROCEEDINGS OF IEEE                                                                                                                            11



   An interesting RL based approach for scheduling paral-               TABLE III: Example code features used in prior works.
lel OpenMP programs is presented in [110]. This approach               Description                      Examples
predicts the best number of threads for a target OpenMP
                                                                       Arithmetic instructions          #floating point instr., #integer instr.,
program when it runs with other competing workloads, aiming                                             #method call instr.
to make the target program run faster. This approach first             Memory operations                #load instr, #store instr.
learns a reward function offline based on static code features         Branch instructions              #conditional branch instr, #uncon-
                                                                                                        ditional branch instr
and runtime system information. The reward function is used            loop information                 #loops, loop depth
to estimate the reward of a runtime scheduling action, i.e.            parallel information             #work threads, work group size
the expected speedup when assigning a certain number of
processor cores to an OpenMP program. In the next scheduling
epoch, this approach uses the empirical observation of the               One technique that has seen little investigation is the use
applications speedup to check if the reward function was              of Gaussian Processes [112]. Before the recent widespread
accurate and the decision was good, and update the reward             interest in deep neural networks, these were a highly popular
function if the model is found to be inaccurate.                      method in many areas of machine learning [113]. They are
   In general, RL is an intuitive and comprehensive solution          particular powerful when the amount of training data is sparse
for autonomous decision making. But its performance depends           and expensive to collect. They also automatically give a
on the effectiveness of the value function, which estimates the       confidence interval with any decision. This allows the compiler
immediate reward. An optimal value function should lead to            writer to trade off risk vs reward depending on application
the greatest cumulative reward in the longer term. For many           scenario,
problems, it is difficult to design an effective value function or       Using a single model has a significant drawback in practice.
policy, because the function needs to foresee the impact of an        This is because a one-size-fits-all model is unlikely to precisely
action in the future. In recent years, deep learning techniques       capture behaviors of diverse applications, and no matter how
have been used in conjunct with RL to learn a value function.         parameterized the model is, it is highly unlikely that a model
The combined technique is able to solve some problems that            developed today will always be suited for tomorrow. To allow
were deem impossible in the past [111]. However, how to               the model to adapt to the change of the computing environ-
combine deep learning with RL to solve compilation and code           ment and workloads, ensemble learning was exploited in prior
optimisation problems remains an open question.                       works [71], [114], [115]. The idea of ensemble learning is to
                                                                      use multiple learning algorithms, where each algorithm is ef-
D. Discussions                                                        fective for particular problems, to obtain better predictive per-
   What model is best, is the $64,000 question. The answer            formance than could be obtained from any of the constituent
is: it depends. More sophisticated techniques may provide             learning algorithm alone [116], [117]. Making a prediction
greater accuracy but they require large amounts of labelled           using an ensemble typically requires more computational time
training data - a real problem in compiler optimisation.              than doing that using a single model, so ensembles can be
Techniques like linear regression and decision trees require          seen as a way to compensate for poor learning algorithms
less training data compared to more advanced models like              by performing extra computation. To reduce the overhead,
SVMs and ANNs. Simple models typically work well when                 fast algorithms such as decision trees are commonly used
the prediction problem can be described using a feature vector        in ensemble methods (e.g. Random Forests), although slower
that has a small number of dimensions, and when the feature           algorithms can benefit from ensemble techniques as well.
vector and the prediction is linearly correlated. More advanced
techniques like SVMs and ANNs can model both linear and                                  V. F EATURE E NGINEERING
non-linear problems on a higher dimensional feature space,               Machine learning based code optimisation relies on hav-
but they often require more training data to learn an effective       ing a set of high-quality features that capture the important
model. Furthermore, the performance of a SVM and an ANN               characteristics of the target program. Given that there is an
also highly depends the hyper-parameters used to train the            unbounded number of potential features, finding the right set
model. The optimal hyper-parameter values can be chosen               is a non-trivial task. In this section, we review how previous
by performing cross-validation on the training data. However,         work chooses features, a task known as feature engineering.
how to select parameters to avoid over-fitting while achieving
a good prediction accuracy remains an outstanding challenge.
   Choosing which modelling technique to use is non-trivial.          A. Feature representation
This is because the choice of model depends on a number of               Various forms of program features have been used in
factors: the prediction problem (e.g. regression or classifica-       compiler-based machine learning. These include static code
tion), the set of features to use, the available training examples,   structures [118] and runtime information such as system
the training and prediction overhead, etc. In prior works, the        load [114], [119] and performance counters [51].
choice of modelling technique is largely relied on developer             1) Static code features: Static program features like the
experience and empirical results. Many of the studies in the          number and type of instructions are often used to describe
field of machine learning based code optimisation do not fully        a program. These features are typically extracted from the
justify the choice of the model, although some do compare the         compiler intermediate representation [44], [27], [50], [78] in
performance of alternate techniques.                                  order to avoid using information extracted from dead code.

PROCEEDINGS OF IEEE                                                                                                                                12




                              Application      dynamic program features (e.g. loop   tracted from multiple layers of the runtime environment. At
                                               counts, hot code etc.)
   01010
                                                                                     the application layer, we can obtain information like loop iter-
                            Operating System   OS info. (e.g. I/O contention, CPU
           profiling runs
                                               loads)
                                                                                     ation counts the cannot be decided at compile time, dynamic
Program binary                 Hardware        Performance counter values (e.g.      control flows, frequently executed code regions, etc. At the
                                               #instr., #L1 cache misses)            operating system level, we can observe the memory and I/O
Fig. 12: Dynamic features can be extracted from multiple                             behaviour of the application as well as CPU load and thread
layers of the computing environment.                                                 contention, etc. At the hardware level, we can use performance
                                                                                     counters to track information like how many instructions have
                                                                                     been executed and of what types, and the number of cache
Table III gives some of the static code features that were used                      loads/stores as well as branch misses, etc.
in previous studies. Raw code features are often used together                          Hardware performance counter values like executed in-
to create a combined feature. For example, one can divide the                        struction counts and cache miss rate are therefore used to
number of load instructions by the number of total instructions                      understand the application’s dynamic behaviours [51], [123].
to get the memory load ratio. An advantage of using static                           These counters can capture low-level program information
code features is that the features are readily available from                        such as data access patterns, branches and computational
the compiler intermediate representation.                                            instructions. One of the advantage of performance counters
   2) Other static features: Singer and Veloso represent the                         is that they capture how the target program behave on a
FFT in a split tree [120]. They extract from the tree a set                          specific hardware and avoid the irrelevant information that
of features, by counting the number of nodes of various types                        static code features may bring in. In addition to hardware
and quantifying the shape of the tree. These tree-based features                     performance counters, operating system level metrics like
are then used to build a neural network based cost function                          system load and I/O contention are also used to model an
that predicts which of the two FFT formulas runs faster.                             application’s behavior [37], [119]. Such information can be
The cost function is used to search for the best-performing                          externally observed without instrumenting the code, and can
transformation.                                                                      be obtain during off-line profiling or program execution time.
   Park et al. present a unique graph-based approach for feature                        While effective, collecting dynamic information could incur
representations [121]. They use a SVM where the kernel is                            prohibitively overhead and the collected information can be
based on a graph similarity metric. Their technique requires                         noisy due to competing workloads and operating system
hand coded features at the basic block level, but thereafter,                        scheduling [124] or even subtle settings of the execution
graph similarity against each of the training programs takes                         environment [125]. Another drawback of performance coun-
the place of global features. Mailike shows that spatial based                       ters and dynamic features is that they can only capture
information, i.e. how instructions are distributed within a                          the application’s past behavior. Therefore, if the application
program, extracted from the program’s data flow graph could                          behaves significantly different in the future due to the change
be useful features for machine learning based compiler optimi-                       of program phases or inputs, then the prediction will be drawn
sation [122]. Nobre et al. also exploit graph structures for code                    on an unreliable observation. As such, dynamic and static
generation [24]. Their approach targets the phase ordering                           features are often used in combination in prior works in order
problem. The order of compiler optimisation passes is repre-                         to build a robust model.
sented as a graph. Each node of the graph is an optimisation
pass and connections between nodes are weighted in a way                             B. Reaction based features
that sub-sequences with higher aggregated weights are more                              Cavazos et al. present a reaction-based predictive model for
likely to lead to faster runtime. The graph is automatically                         software-hardware co-design [126]. Their approach profiles
constructed and updated using iterative compilation (where                           the target program using several carefully selected compiler
the target program is complied using different compiler passes                       options to see how program runtime changes under these
with different orders). A design space exploration algorithm                         options for a given micro-architecture setting. They then use
is employed to drive the iterative compilation process.                              the program “reactions” to predict the best available applica-
   3) Dynamic Features: While static code features are useful                        tion speedup. Figure 13 illustrates the difference between a
and can be extracted at static compile time (hence feature                           reaction-based model and a standard program feature based
extraction has no runtime overhead), they have drawbacks.                            model. A similar reaction-based approach is used in [127] to
For examples, static code features may contain information                           predict speedup and energy efficiency for an application that
of code segments that rarely get executed, and such in-                              is parallelised thread-level speculation (TLS) under a given
formation can confuse the machine learning model; some                               micro-architectural configuration. Note that while a reaction-
program information such as the loop bound depends on the                            based approach does not use static code features, developers
program input, which can only obtained during execution time;                        must carefully select a few settings from a large number of
and static code features often may not precisely capture the                         candidate options for profiling, because poorly chosen options
application behaviour in the runtime environment (such as                            can significantly affect the quality of the model.
resource contention and I/O behaviour) as such behaviour
highly depends on the computing environment such as the                              C. Automatic feature generation
number of available processors and co-running workloads.                               As deriving good features is a time-consuming task, a few
   As illustrated in Figure 12, dynamic features can be ex-                          methods have been proposed to automatically generate features

 PROCEEDINGS OF IEEE                                                                                                                                                           13



                                                                                                                   tioning that dynamic information such as the program input




                                                                            Predictive Model
                       ...                                                                                         size and performance counter values are often essential for
             Candiate compiler                                                                           Predicted
                                                                                                                   characterising the behaviour of the target program. Therefore,
              transformation                                                                             speedup DeepTune does not completely remove human involvement for
                                 Transformed code
 Program source                                 Static program                                                     feature engineering when static code features are insufficient
                                                features                                                           for the optimisation problem.
                   (a) Static program feature based predictor
                                                            ...      Candidate compiler
                                                      ...         Candidate compiler
                                                                                  D. Feature selection and dimension reduction
                                                                   transformation
                                                 (010000111000) transformation
                                               (010000111000)                        Machine learning uses features to capture the essential

                                 t1
                                                                                  characteristics of a training example. Sometimes we have
                                 t1
                    ......                                   s1 s1                too many features. As the number of features increase so




                                                                                           Predictive Model
                                                                                Predictive Model
                                    ...
                                   ...
                                                                                  does the number of training examples needed to build an
                                                             s2 s2
                                    Hardware
                                     Hardware




                                  t2                                   Predicted
                                                                            Predicted
                                  t2
                                                                                  accurate model [129]. Hence, we need to limit the dimension
                                                                       speedup
                                                                             speedup
                                                             s3 s3                of the feature space In compiler research, commonly, an initial
  Programsource
Program   source           .
                           .....
                                                    Measured speedups
                                                                                  large, high dimensional candidate feature space is pruned via
                                        t3           Measured speedups
                Selected compiler        t3             (reactions)
                                                           (reactions)
                                                                                  feature selection [50], or projected into a lower dimensional
              transforms (t1, t2, t3)                                             space [15]. In this subsection, we review a number of feature
                                      (b) Reaction based predictor                selection and dimension reduction methods.
                                                                                     1) Feature selection: Feature selection requires understand-
  Fig. 13: Standard feature-based modeling (a) vs reaction-based
                                                                                  ing how does a particular feature affect the prediction accuracy.
  modeling (b). Both models try to predict the speedup for a
                                                                                  One of the simplest methods for doing this is applying the
  given compiler transformation sequence. The program feature
                                                                                  Pearson correlation coefficient. This metric measures the linear
  based predictor takes in static program features extracted from
                                                                                  correlation between two variables and is used in numerous
  the transformed program, while the reaction based model
                                                                                  works [130], [53], [118], [90] to filter out redundant features
  takes in the target transformation sequence and the measured
                                                                                  by removing features that have a strong correlation with an
  speedups of the target program, obtained by applying a number
                                                                                  already selected feature. It has also been used to quantify
  of carefully selected transformation sequences. Diagrams are
                                                                                  the relation of the select features in regression. One obvious
  reproduced from [126].
                                                                                  drawback of using Pearson correlation as a feature ranking
                                                                                  mechanism is that it is only sensitive to a linear relationship.
                                                                                     Another approach for correlation estimation is mutual infor-
  from the compiler’s intermediate representation (IR) [128], mation [126], [131], which quantifies how much information
  [68]. The work of [68] uses GP to search for features, but of one variable (or feature) can be obtained through another
  required a huge grammar to be written, some 160kB in length. variable (feature). Like correlation coefficient, mutual informa-
  Although much of this can be created from templates, selecting tion can be used to remove redundant features. For example, if
  the right range of capabilities and search space bias is non triv- the information of feature, x, can be largely obtained through
  ial and up to the expert. The work of [128] expresses the space another existing feature, y, feature x can then be taken out
  of features via logic programming over relations that represent from the feature set without losing much information on the
  information from the IRs. It greedily searches for expressions reduced feature set.
  that represent good features. However, their approach relies                       Both correlation coefficient and mutual information evaluate
  on expert selected relations, combinators and constraints to each feature independently with respect to the prediction. A
  work. Both approaches closely tie the implementation of the different approach is to utilise regression analysis for feature
  predictive model to the compiler IR, which means changes to ranking. The underlying principal of regression analysis is
  the IR will require modifications to the model. Furthermore, that if the prediction is the outcome of regression model
  the time spent in searching features could be significant for based on the features, then the most important features should
  these approaches.                                                               have the highest weights (or coefficients) in the model, while
     The first work to employ neural network to extract fea- features uncorrelated with the output variables should have
  tures from program source code for compiler optimisation weights close to zero. For example, LASSO (least absolute
  is conducted by Cummin et al. [76]. Their system, name- shrinkage and selection operator) regression analysis is used
  ly DeepTune, automatically abstracts and selects appropriate in [132] to remove less useful features to build a compiler-
  features from the raw source code. Unlike prior work where based model to predict performance. LASSO has also been
  the predictive model takes in a set of human-crafted features, used for feature selection to tune the compiler heuristics for
  program code is used directly in the training data. Programs the TRIPS processor [133].
  are fed through a series of neural network based language                          In general, feature selection remains an open problem
  models which learn how code correlates with the desired for machine learning, and researchers often follow a “trail-
  optimisation options (see also Figure 8). Their work also and-error” approach to test a range of methods and feature
  shows that the properties of the raw code that are abstracted by candidates. This makes automatic feature selection framework
  the top layers of the neural networks are mostly independent like FEAST [134] and HERCULES [135] attractive. The for-
  of the optimisation problem. While promising, it is worth men- mer framework employs a range of existing feature selection

PROCEEDINGS OF IEEE                                                                                                                  14



         M3                                                           correlated with one another. Similar feature reduction methods
                                                                      include factor analysis and linear discriminant analysis (LDA),
                              PC
                                 1
                                                                      which all try to reduce the number of features by linearly
                                                                      combining multiple raw features. However, PCA seems to be
                                                                      the most popular feature reduction method used in compiler
                                                                      research, probably due to its simplicity.
                PC
                   3
                                    M
                                                                         An alternative way of reducing the number of features used




                                            PC2
                                     2
                                                                      is via an autoencoder [139]. It is a neural network that finds a
                       PC



                                                     PC1
                                                                      representation (encoding) for a set of data, by dimensionality
  M1




                          2




                                                                      reduction. Autoencoders works by learning an encoder and
                                                                      a decoder from the input data. The encoder tries to compress
       (a) Original feature space        (b) Reduced feature space    the original input into a low-dimensional representation, while
Fig. 14: Using PCA to reduce dimensionality of a three-               the decoder tries to reconstruct the original input based on the
dimensional feature space. The principal components are first-        low-dimension representations generated by the encoder. As
ly computed (a). Then the first two principal components              a result, the autoencoder has been widely used to remove the
(P C1 and P C2 ) are selected to represent the original three-        data noise as well to reduce the data dimension [140].
dimensional feature space on a new two-dimensional space b.              Autoencoders have been applied to various natural language
                                                                      processing tasks [97], often being used together with DNNs.
                                                                      Recently, it has been employed to model program source code
                                                                      to obtain a compact set of features that can characterise the
methods to select useful candidate features, while the latter
                                                                      input program source [141], [142], [87], [76], [143].
searches for the most important static code features from a set
of pre-defined patterns for loops.
   2) Feature dimensionality reduction: While feature selec-                                    VI. S COPE
tion allows us to select the most important features, the                Machine learning has been used to solve a wide range of
resulted feature set can still be too large to train a good model,    problems, from the early successful work of selecting compiler
especially when we only have a small number of training               flags for sequential programs, to recent works on scheduling
examples. By reducing the number of dimensions, the learning          and optimising parallel programs on heterogeneous multi-
algorithm can often perform more efficiently on a limited             cores. In this section, we review the types of problems that
training dataset. Dimension reduction is also important for           have been exploited in prior works.
some machine learning algorithms such as KNN to avoid the
effect of the curse of dimensionality [136].
   PCA is a well-established feature reduction technique [137].       A. Optimise sequential programs
It uses orthogonal linear transformations to reduce the dimen-           Early works for machine learning in compilers look at how,
sionality of a set of variables i.e. features in our case.            or if, a compiler optimisation should be applied to a sequen-
   Figure 14 demonstrates the use of PCA to reduce the                tial program. Some of the previous studies build supervised
number of dimensions. The input in this example is a three-           classifiers to predict the optimal loop unroll factor [68], [50]
dimensional space defined by M1 , M2 and M3 , as shown in             or to determine whether a function should be inlined [27],
Figure 14 (a). Three components: P C1 , P C2 and P C3 , which         [33]. These works target a fixed set of compiler options,
account for the variance of the data, are firstly calculated. Here,   by representing the optimisation problem as a multi-class
P C1 and P C2 contribute most to the variance of the data and         classification problem – where each compiler option is a class.
P C3 accounts for the least variance. Using only P C1 and             For example, Leather et al. [68] considered a loop unroll factor
P C2 , one can transform the original, three-dimensional space        between 0 and 15 (16 configurations in total), treating each
into a new, two-dimensional coordinate system (as illustrated         candidate unroll factor as a class; they compiled and profiled
in Figure 14b) while preserving much of the variance of the           each training program by trying all 16 configurations to find
original data.                                                        out the best loop unroll factor for each program, and then
   PCA has been used in many prior compiler research works            learned a decision tree model from the training data.
for feature reduction [93], [23], [53], [94], [90], [95], [138],         There are other compiler problems where the number of
[15]. It has also been used in prior works to visualise the           possible options is massive. For instance, the work presented
working mechanism of a machine learning model, e.g. to show           in [53] considers 54 code transformations of GCC. While these
how benchmarks can be grouped in the feature space [119],             options are only a subset from the over 100s transformations
by projecting features from a high-dimensional space into a           provided by GCC, the resulted combinatorial compiler con-
2-dimensional space.                                                  figurations lead to a space of approximately 1034 . Although it
   We want to stress that PCA does not select some features and       is possible to build a classifier to directly predict the optimal
discard the others. Instead, it linearly combines the original        setting from a large space, to learn an effective model would
features to construct new features that can summarise the list        require a large volume of training programs in order to have an
of the original features. PCA is useful when there is some            adequate sampling over the space. Doing so is difficult because
redundancy in the raw features, i.e. some of the features are         (a) there are only a few dozen common benchmarks available

PROCEEDINGS OF IEEE                                                                                                                15



and (b) compiler developers need to generate the training data       candidate transformed graphs (without compiling and profiling
themselves.                                                          the resulted graphs) in the original feature space.
   Evolutionary algorithms like generic search are often used           The Petabricks project [101], [160], [161] developed at
to explore a large design space (see also Section IV-C1). Prior      MIT takes an evolutionary approach for program tuning. The
works have used evolutionary algorithms to solve the phase           Petabricks compiler employs genetic search algorithms to tune
ordering problem (i.e. at which order a set of compiler trans-       algorithmic choices. Due to the expensive overhead of the
formations should be applied) [144], [145], [146], determining       search, much of auto-tuning is done at static compile time.
the compiler flags during iterative compilation [147], [148],        Their work shows that one can utilise the idle processors on
[149], [150], selecting loop transformations [151], and tuning       a multi-core systems to perform online tuning [162], where
algorithmic choices [101], [11], etc.                                half of the cores are devoted to a known safe program
                                                                     configuration, while the other half are used for an experimental
                                                                     program configuration. In this way, when the results of the
B. Optimise parallel programs
                                                                     faster configuration are returned, the slower version will be
   How to effectively optimise parallel programs has received        terminated.
significant attentions in the past decade, largely because the          There is also an extensive body of work on how to opti-
hardware industry has adopted multi-core design to avoid the         mise programs on heterogeneous multi-core systems. One of
power wall [152]. While multi- and many-core architectures           the problems for heterogeneous multi-core optimisation is to
provide the potential for high performance and energy-efficient      determine when and how to use the heterogeneous processors.
computing, the potential performance can only be unlocked if         Researchers have used machine learning to build classifiers to
the application programs are suitably parallel and can be made       determine which processor to use [66] and at which clock fre-
to match the underlying heterogeneous platform. Without this,        quency the processor should operate [78], [163]. Others used
the myriad cores on multi-core processors and their specialised      regression techniques to build curve fitting models to search
processing elements will sit idle or poorly utilised. To this        for the sweat spot for work partitioning among processors [36]
end, researchers have extended the reach of machine learning         or a trade-off of energy and performance [164].
to optimise parallel programs.                                          Another line of research combines compiler-based analysis
   A line of research in parallel program optimisation is            and machine learning to optimise programs in in the presence
parallelism mapping. That is, given an already parallelised          of competing workloads. This research problem is important
program, how to map the application parallelism to match             because programs rarely run in isolation and must share
the underlying hardware to make the program runs as fast             the computing resources with other co-running workloads.
as possible or be as energy-efficient as possible. Zhang et          In [165] and [166], an ANN model based on static code
al. developed a decision tree based approach to predict the          features and runtime information was built to predict the
scheduling policy to use for an OpenMP parallel region [153].        number of threads to use for a target program when it runs
The work presented in [44] employs two machine learning              with external workloads. Later in [114] an ensemble learning
techniques to predict the optimal number of threads as well          based approach was used, which leads to significantly better
as the scheduling policy to use for OpenMP parallel loop.            performance over [165]. In [114] several models are firstly
Specifically, it uses a regression-based ANN model to predict        trained offline; and then one of the model is selected at run-
the speedup of a parallel loop when it runs with a given             time, taking into consideration the competing workloads and
number of threads (to search for the optimal number threads),        available hardware resources. The central idea is that instead
and a SVM classifer to predict the scheduling policy. There are      of using a single monolithic model, we can use multiple
also works use machine learning to determine the optimum             models where each model is specialised for modeling a subset
degree of parallelism for transactional memory [154] and             of applications or a particular runtime scenario. Using this
hardware source allocation [155], or to select a code version        approach, a model is used when its predictions are effective.
from a pool of choices to use [156]. Castro et al. developed a          Some recent works developed machine learning models
decision tree classifier to predict the thread mapping strategy      based on static code features and dynamic runtime informa-
in the context of software transactional memory [157]. Jung          tion to schedule OpenCL programs in the presence of GPU
et al. constructed a ANN based predictor to select an effective      contention. The work presented in uses SVM classification to
data structure on a specific micro-architecture [158].               predict the work partition ratio between the CPU and GPU
   The work presented in [90] and [159] is a unique approach         when multiple programs are competing to run on a single
for applying machine learning to map complex parallel pro-           GPU [167]. The work described in [37] aims to improve the
grams with unbounded parallel graph structures. The work             overall system throughput when there are multiple OpenCL
considers the question of finding the optimal graph structure        programs competing to run on the GPU. They developed an
of a streaming program. The idea was that rather than trying         ANN model to predict the potential speedup for running an
to predict a sequence of transformations over an unbounded           OpenCL kernel on the GPU. The speedup prediction is then
graph, where legality and consistency is a real problem, we          used as a proxy to determine which of the waiting OpenCL
should consider the problem from the dual feature space. The         tasks get to run on the GPU and at which order.
work showed that it is possible to predict the best target feature      The approaches presented in [168] and [169] target task co-
(i.e. the characteristics that an ideal transformed program          location in a data center environment. They use compiler based
should have) which then can be used to evaluate the worth of         code transformations to reduce the contention for multiple co-

PROCEEDINGS OF IEEE                                                                                                              16



running tasks. A linear regression model was employed to          any new heuristic should outperform this – though in our
calculate the contention score of code regions based on per-      experience there have been cases where state-of the art work
formance counter values. Then, a set of compiler-based code       was actually less than random.
transformations is applied to reduce the resource demands of
highly contentious code.                                          A. Not a panacea
                                                                     This article has by and large been very upbeat about the use
C. Other research problems                                        of machine learning. However, there are number of hurdles to
   There are many works have demonstrated that machine            overcome to make it a practical reality and opens up new
learning is a powerful technique in performance and cost          questions about optimisation
modelling [170], [171], [172], [45], and in task and resource        Training cost is an issue that many find alarming. In practise
scheduling [173], [155], [174], [175]. We envision that many      the cost is much less than a compiler writer and techniques like
of these techniques can be used to provide evidences to           active learning can be employed to reduce overhead of training
support runtime program optimisations through e.g. just-in-       data generation [183], [184], [185], [186]. Although its true
time compilation.                                                 to say that generating many differently compiled programs
   While not directly target code optimisation, compiler based    executing and timing them is entirely automatic, finding the
code analysis and machine learning techniques have been           right data requires careful consideration. If the optimisations
used in conjunction to solve various software engineering         explored have little positive performance on the programs then
tasks. These include detecting code similarities [176], [177],    there is nothing worth learning.
automatic comment generation [178], mining API usage pat-            The most immediate problem continues to be gathering
terns [179], [180], predicting program properties [181], code     enough sufficient high quality training data. Although there
de-obfuscation for malware detection [182], etc. It is worth      are numerous benchmark sites publicly available, the number
mentioning that many of these recent works show that the          of programs available is relatively sparse compared to to the
past development knowledge extracted from large code bases        number a typical compiler will encounter in its lifetime. This
such as GitHub are valuable for learning an effective model.      is particular true in specialist domains where there may not
There were two recent studies performed by Cummin et al.,         be any public benchmarks. Automatic benchmark generation
which mine Github to synthesize OpenCL benchmarks [87]            work will help here, but the larger issue of the structure of the
and code extract features from source code [76]. Both studies     the program space remain
demonstrate the usefulness of large code bases and deep              A really fundamental problem is that if we build our
learning techniques for learning predictive models for compiler   optimisation models based purely on empirical data, then we
optimisations. We envision that the rich information in large     must guarantee that this data is correct and representative; we
open source code bases could provide a powerful knowledge         must learn the signal not the noise. Peer review of machine
base for training machine learning models to solve compiler       learning approach is difficult. Black box modelling prevents
optimisation problems, and deep learning could be used as an      the quality of the model from being questioned unlike hand-
effective tool to extract such knowledge from massive program     crafted heuristics. In a sense reviewers now have to scrutinise
source code.                                                      that the experiments were fairly done. This means all training
                                                                  and test data must be publicly available for scrutiny. This
                      VII. D ISCUSSION                            is common practise in other empirical sciences. The artefact
                                                                  evaluation committee is an example of this [187], [188].
   One of the real benefits of machine learning based approach-
                                                                     Although the ability to automatically learn how to best opti-
es is that it forces an empirical driven approach to compiler
                                                                  mise an application and adapt to change is a big step forward,
construction. New models have to be based on empirical data
                                                                  machine learning can only learn form what is provided by
which can then be verified by independent experimentation.
                                                                  the compiler writer. Machine learning can not invent new
This experiment – hypothesis – test cycle is well known in
                                                                  program transformations to apply nor can it derive analysis
the physical sciences but is a relatively new addition compiler
                                                                  that determines whether or not a transformation is legal – all
construction.
                                                                  of this is beyond its scope.
   As machine learning based techniques require a sampling
of the optimisation space for training data, we typically know
the best optimisation for any program in the training set. If     B. Will this put compiler writer out of a job?
we exclude this benchmark from training, we therefore have           In fact machine learning based compilation will paradoxi-
access to an upper bound on performance or oracle for this        cally lead to a renaissance in compiler optimisation. Compiler
program. This immediately lets us know how good existing          have become so complex that adding a new optimisation or
techniques are. If they are 50% of this optimum or 95% of this    compiler phase can lead to performance regressions. This in
optimum immediately tells us whether the problem is worth         turn has led to a conservative mind set where new transfor-
exploring.                                                        mations are not considered if they may rock the boat. The
   Furthermore we can construct naive techniques – e.g. a         core issue is that systems are so complex that is impossible
random optimisation and see its performance. If this performed    to know for sure when to use or not such an optimisation.
a number of times, it will have an expected value of the          Machine learning can remove this uncertainty by automatically
mean of the optimisation speedups. We can then demand that        determining when an optimisation is profitable. This now

PROCEEDINGS OF IEEE                                                                                                                                        17



frees the compiler writer to develop ever more sophisticated                    [4] A. Gauci, K. Z. Adami, and J. Abela, “Machine learning for galaxy
techniques. He/she does not need to worry about how they                            morphology classification,” arXiv preprint arXiv:1005.0390, 2010.
                                                                                [5] H. Schoen, D. Gayo-Avello, P. Takis Metaxas, E. Mustafaraj,
interfere with other optimisations – machine learning looks                         M. Strohmaier, and P. Gloor, “The power of prediction with social
after this. We can now develop optimisations that will typ-                         media,” Internet Research, vol. 23, no. 5, pp. 528–543, 2013.
ically only work for specific domains, and not worry about                      [6] Slashdot.         (2009)       IBM         releases      open       source
                                                                                    machine          learning       compiler.        [Online].      Available:
coordinating their integration into a general purpose system.                       https://tech.slashdot.org/story/09/07/03/0143233/ibm-releases-open-
It allows different communities to develop novel optimisations                      source-machine-learning-compiler
and naturally integrate them. So rather than closing down the                   [7] H. Massalin, “Superoptimizer: a look at the smallest program,” in ACM
                                                                                    SIGPLAN Notices, vol. 22, no. 10, 1987, pp. 122–126.
opportunity for new ideas, it opens up new vistas.                              [8] J. Ivory, “I. on the method of the least squares,” The Philosophical Mag-
                                                                                    azine and Journal: Comprehending the Various Branches of Science,
C. Open research directions                                                         the Liberal and Fine Arts, Agriculture, Manufactures and Commerce,
                                                                                    vol. 65, no. 321, pp. 3–10, 1825.
   Machine learning has demonstrated its utility as a means of                  [9] R. J. Adcock, “A problem in least squares,” The Analyst, vol. 5, no. 2,
automating compiler profitability analysis. It will continue to                     pp. 53–54, 1878.
                                                                               [10] K. Datta, M. Murphy, V. Volkov, S. Williams, J. Carter, L. Oliker,
be used for more complex optimisation problems and is likely                        D. Patterson, J. Shalf, and K. Yelick, “Stencil computation optimization
to be the default approach to selecting compiler optimisations                      and auto-tuning on state-of-the-art multicore architectures,” in Proceed-
in the coming decade.                                                               ings of the 2008 ACM/IEEE conference on Supercomputing, 2008, p. 4.
                                                                               [11] J. Ansel, Y. L. W. ans Cy Chan, M. Olszewski, A. Edelman, and
   The open research directions go beyond predicting the best                       S. Amarasinghe, “Language and compiler support for auto-tuning
optimisations to apply. One central issue is what does the                          variable-accuracy algorithms,” in The International Symposium on
program space look like? We know that programs with linear                          Code Generation and Optimization, ser. CGO ’11, 2011.
                                                                               [12] M. E. Lesk and E. Schmidt, “Lex: A lexical analyzer generator,” 1975.
array accesses inside perfect loop nests need different treat-
                                                                               [13] S. C. Johnson, Yacc: Yet another compiler-compiler. Bell Laboratories
ment compared to, say, distributed graph processing programs.                       Murray Hill, NJ, 1975, vol. 32.
If we could have a map that allows us to measure distances                     [14] A. Monsifrot, F. Bodin, and R. Quiniou, “A machine learning approach
between programs, then we could see whether there are regions                       to automatic production of compiler heuristics,” in International Con-
                                                                                    ference on Artificial Intelligence: Methodology, Systems, and Applica-
that are well served by compiler characterise and other regions                     tions, 2002, pp. 41–50.
that are sparse and currently ignored. If we could do the same                 [15] A. Magni, C. Dubach, and M. O’Boyle, “Automatic optimization of
for hardware, then we may be better able to design hardware                         thread-coarsening for graphics processors,” in Proceedings of the 23rd
                                                                                    International Conference on Parallel Architectures and Compilation,
likely to be of use for emerging applications.                                      ser. PACT ’14, 2014, pp. 455–466.
   Can machine learning also be applied to compiler analy-                     [16] S. Unkule, C. Shaltz, and A. Qasem, “Automatic restructuring of GPU
sis? For instance is it possible to learn dataflow or point-to                      kernels for exploiting inter-thread data locality,” in Proceedings of the
                                                                                    21st International Conference on Compiler Construction, ser. CC’12,
analysis? As deep learning has the ability to automatically                         2012, pp. 21–40.
constructs features, can we find a set of features that are                    [17] V. Volkov and J. W. Demmel, “Benchmarking GPUs to tune dense
common across all optimisations and analyses. Can we learn                          linear algebra,” in Proceedings of the 2008 ACM/IEEE Conference on
                                                                                    Supercomputing, ser. SC ’08, 2008, pp. 31:1–31:11.
the ideal compiler intermediate representation?                                [18] Y. Yang, P. Xiang, J. Kong, M. Mantor, and H. Zhou, “A unified
                                                                                    optimizing compiler framework for different gpgpu architectures,”
                        VIII. C ONCLUSION                                           ACM Trans. Archit. Code Optim., vol. 9, no. 2, pp. 9:1–9:33, 2012.
                                                                               [19] C. Lattner and V. Adve, “LLVM: A compilation framework for lifelong
   This paper has introduced machine learning based compila-                        program analysis & transformation,” in Proceedings of the Interna-
tion and described its power in determining an evidence based                       tional Symposium on Code Generation and Optimization: Feedback-
approach to compiler optimisation. It is the latest stage in                        directed and Runtime Optimization, ser. CGO ’04, 2004.
                                                                               [20] F. Bodin, T. Kisuki, P. Knijnenburg, M. O’Boyle, and E. Rohou,
fifty years of compiler automation. Machine learning based                          “Iterative compilation in a non-linear optimisation space,” in Workshop
compilation is now a mainstream compiler research area and                          on Profile and Feedback-Directed Compilation, 1998.
over the last decade or so, has generated a large amount of                    [21] P. M. Knijnenburg, T. Kisuki, and M. F. O’Boyle, “Combined selection
                                                                                    of tile sizes and unroll factors using iterative compilation,” The Journal
academic interest and papers. While it is impossible to provide                     of Supercomputing, vol. 24, no. 1, pp. 43–67, 2003.
a definitive cataloguer of all research, we have tried to provide              [22] M. Frigo and S. G. Johnson, “The design and implementation of
a comprehensive and accessible survey of the main research                          FFTW3,” Proceedings of the IEEE, vol. 93, no. 2, pp. 216–231, 2005,
                                                                                    special issue on “Program Generation, Optimization, and Platform
areas and future directions. Machine learning is not a panacea.                     Adaptation”.
It can only learn the data we provide. Rather than, as some                    [23] F. Agakov, E. Bonilla, J. Cavazos, B. Franke, G. Fursin, M. F. P.
fear, it dumbs down the role of compiler writers, it opens up                       O’Boyle, J. Thomson, M. Toussaint, and C. K. I. Williams, “Using
                                                                                    machine learning to focus iterative optimization,” in Proceedings of
the possibility of much greater creativity and new research                         the International Symposium on Code Generation and Optimization,
areas.                                                                              ser. CGO ’06, 2006, pp. 295–305.
                                                                               [24] R. Nobre, L. G. A. Martins, and J. a. M. P. Cardoso, “A graph-
                                                                                    based iterative compiler pass selection and phase ordering approach,”
                             R EFERENCES                                            in Proceedings of the 17th ACM SIGPLAN/SIGBED Conference on
  [1] J. Chipps, M. Koschmann, S. Orgel, A. Perlis, and J. Smith, “A                Languages, Compilers, Tools, and Theory for Embedded Systems, ser.
      mathematical language compiler,” in Proceedings of the 1956 11th              LCTES 2016, 2016, pp. 21–30.
      ACM national meeting. ACM, 1956, pp. 114–117.                            [25] R. Leupers and P. Marwedel, “Function inlining under code size con-
  [2] P. B. Sheridan, “The arithmetic translator-compiler of the ibm fortran        straints for embedded processors,” in Computer-Aided Design, 1999.
      automatic coding system,” Communications of the ACM, vol. 2, no. 2,           Digest of Technical Papers. 1999 IEEE/ACM International Conference
      pp. 9–21, 1959.                                                               on. IEEE, 1999, pp. 253–256.
  [3] M. D. McIlroy, “Macro instruction extensions of compiler languages,”     [26] K. D. Cooper, T. J. Harvey, and T. Waterman, “An adaptive strategy for
      Communications of the ACM, vol. 3, no. 4, pp. 214–220, 1960.                  inline substitution,” in Proceedings of the Joint European Conferences

PROCEEDINGS OF IEEE                                                                                                                                       18



     on Theory and Practice of Software 17th International Conference on        [46] L. Benini, A. Bogliolo, M. Favalli, and G. De Micheli, “Regression
     Compiler Construction, ser. CC’08/ETAPS’08, 2008, pp. 69–84.                    models for behavioral power estimation,” Integr. Comput.-Aided Eng.,
[27] D. Simon, J. Cavazos, C. Wimmer, and S. Kulkarni, “Automatic con-               vol. 5, no. 2, pp. 95–106.
     struction of inlining heuristics using machine learning,” in Proceedings   [47] S. K. Rethinagiri, R. B. Atitallah, and J. L. Dekeyser, “A system
     of the 2013 IEEE/ACM International Symposium on Code Generation                 level power consumption estimation for mpsoc,” in 2011 International
     and Optimization (CGO), ser. CGO ’13, 2013, pp. 1–12.                           Symposium on System on Chip (SoC), 2011, pp. 56–61.
[28] P. Zhao and J. Amaral, “To inline or not to inline? enhanced inlining      [48] S. Schürmans, G. Onnebrink, R. Leupers, G. Ascheid, and X. Chen,
     decisions,” Languages and Compilers for Parallel Computing, pp. 405–            “Frequency-aware esl power estimation for arm cortex-a9 using a black
     419, 2004.                                                                      box processor model,” ACM Trans. Embed. Comput. Syst., vol. 16,
[29] T. A. Wagner, V. Maverick, S. L. Graham, and M. A. Harrison,                    no. 1, pp. 26:1–26:26, 2016.
     “Accurate static estimators for program optimization,” in Proceedings      [49] M. Curtis-Maury, K. Singh, S. A. McKee, F. Blagojevic, D. S.
     of the ACM SIGPLAN 1994 Conference on Programming Language                      Nikolopoulos, B. R. de Supinski, and M. Schulz, “Identifying energy-
     Design and Implementation, ser. PLDI ’94, 1994, pp. 85–96.                      efficient concurrency levels using machine learning,” in 2007 IEEE
[30] V. Tiwari, S. Malik, and A. Wolfe, “Power analysis of embedded soft-            International Conference on Cluster Computing, 2007, pp. 488–495.
     ware: A first step towards software power minimization,” in IEEE/ACM       [50] M. Stephenson and S. Amarasinghe, “Predicting unroll factors using
     International Conference on Computer-Aided Design, 1994, pp. 384–               supervised classification,” in Proceedings of the International Sympo-
     390.                                                                            sium on Code Generation and Optimization, ser. CGO ’05, 2005, pp.
[31] K. D. Cooper, P. J. Schielke, and D. Subramanian, “Optimizing for               123–134.
     reduced code space using genetic algorithms,” in Proceedings of the        [51] J. Cavazos, G. Fursin, F. Agakov, E. Bonilla, M. F. P. O’Boyle,
     ACM SIGPLAN 1999 Workshop on Languages, Compilers, and Tools                    and O. Temam, “Rapidly selecting good compiler optimizations using
     for Embedded Systems, ser. LCTES ’99, 1999, pp. 1–9.                            performance counters,” in Proceedings of the International Symposium
[32] M. Stephenson, S. Amarasinghe, M. Martin, and U.-M. O’Reilly, “Meta             on Code Generation and Optimization, ser. CGO ’07, 2007.
     optimization: Improving compiler heuristics with machine learning,” in     [52] J. Cavazos and M. F. P. O’Boyle, “Method-specific dynamic compi-
     Proceedings of the ACM SIGPLAN 2003 Conference on Programming                   lation using logistic regression,” in Proceedings of the 21st Annual
     Language Design and Implementation, ser. PLDI ’03, 2003, pp. 77–90.             ACM SIGPLAN Conference on Object-oriented Programming Systems,
[33] J. Cavazos and M. F. P. O’Boyle, “Automatic tuning of inlining                  Languages, and Applications, ser. OOPSLA ’06, 2006, pp. 229–240.
     heuristics,” in Proceedings of the 2005 ACM/IEEE Conference on             [53] C. Dubach, J. Cavazos, B. Franke, G. Fursin, M. F. O’Boyle, and
     Supercomputing, ser. SC ’05, 2005.                                              O. Temam, “Fast compiler optimisation evaluation using code-feature
[34] K. Hoste and L. Eeckhout, “Cole: Compiler optimization level ex-                based performance prediction,” in Proceedings of the 4th International
     ploration,” in Proceedings of the 6th Annual IEEE/ACM International             Conference on Computing Frontiers, ser. CF ’07, 2007, pp. 131–142.
     Symposium on Code Generation and Optimization, ser. CGO ’08, 2008,         [54] T. Yuki, L. Renganarayanan, S. Rajopadhye, C. Anderson, A. E.
     pp. 165–174.                                                                    Eichenberger, and K. O’Brien, “Automatic creation of tile size selection
[35] M. Kim, T. Hiroyasu, M. Miki, and S. Watanabe, SPEA2+: Improving                models,” in Proceedings of the 8th Annual IEEE/ACM International
     the Performance of the Strength Pareto Evolutionary Algorithm 2, 2004,          Symposium on Code Generation and Optimization, ser. CGO ’10, 2010,
     pp. 742–751.                                                                    pp. 190–199.
[36] C.-K. Luk, S. Hong, and H. Kim, “Qilin: Exploiting parallelism on
                                                                                [55] A. M. Malik, “Optimal tile size selection problem using machine
     heterogeneous multiprocessors with adaptive mapping,” in Proceedings
                                                                                     learning,” in 2012 11th International Conference on Machine Learning
     of the 42Nd Annual IEEE/ACM International Symposium on Microar-
                                                                                     and Applications, vol. 2, 2012, pp. 275–280.
     chitecture, ser. MICRO 42, 2009, pp. 45–55.
                                                                                [56] R. W. Moore and B. R. Childers, “Building and using application
[37] Y. Wen, Z. Wang, and M. O’Boyle, “Smart multi-task scheduling
     for OpenCL programs on CPU/GPU heterogeneous platforms,” in                     utility models to dynamically choose thread counts,” The Journal of
                                                                                     Supercomputing, vol. 68, no. 3, pp. 1184–1213, 2014.
     21st Annual IEEE International Conference on High Performance
     Computing (HiPC 2014). IEEE, 2014.                                         [57] Y. Liu, E. Z. Zhang, and X. Shen, “A cross-input adaptive framework
[38] E. A. Brewer, “High-level optimization via automated statistical mod-           for GPU program optimizations,” in 2009 IEEE International Sympo-
     eling,” in Proceedings of the Fifth ACM SIGPLAN Symposium on                    sium on Parallel Distributed Processing, 2009, pp. 1–10.
     Principles and Practice of Parallel Programming, ser. PPOPP ’95,           [58] E. Perelman, G. Hamerly, M. Van Biesbrouck, T. Sherwood, and
     1995, pp. 80–91.                                                                B. Calder, “Using simpoint for accurate and efficient simulation,” in
[39] K. Vaswani, M. J. Thazhuthaveetil, Y. N. Srikant, and P. J. Joseph, “Mi-        Proceedings of the 2003 ACM SIGMETRICS International Conference
     croarchitecture sensitive empirical models for compiler optimizations,”         on Measurement and Modeling of Computer Systems, ser. SIGMET-
     in International Symposium on Code Generation and Optimization                  RICS ’03, 2003, pp. 318–319.
     (CGO’07), 2007, pp. 131–143.                                               [59] Y. Zhang, D. Meisner, J. Mars, and L. Tang, “Treadmill: Attributing
[40] B. C. Lee and D. M. Brooks, “Accurate and efficient regression                  the source of tail latency through precise load testing and statistical
     modeling for microarchitectural performance and power prediction,”              inference,” in Proceedings of the 43rd International Symposium on
     in Proceedings of the 12th International Conference on Architectural            Computer Architecture, ser. ISCA ’16, 2016, pp. 456–468.
     Support for Programming Languages and Operating Systems, ser.              [60] B. C. Lee, D. M. Brooks, B. R. de Supinski, M. Schulz, K. Singh, and
     ASPLOS XII, 2006, pp. 185–194.                                                  S. A. McKee, “Methods of inference and learning for performance
[41] E. Park, L.-N. Pouche, J. Cavazos, A. Cohen, and P. Sadayappan,                 modeling of parallel applications,” in Proceedings of the 12th ACM
     “Predictive modeling in a polyhedral optimization space,” in Proceed-           SIGPLAN Symposium on Principles and Practice of Parallel Program-
     ings of the 9th Annual IEEE/ACM International Symposium on Code                 ming, ser. PPoPP ’07, 2007, pp. 249–258.
     Generation and Optimization, ser. CGO ’11, 2011, pp. 119–129.              [61] M. Curtis-Maury, J. Dzierwa, C. D. Antonopoulos, and D. S.
[42] M. Curtis-Maury, A. Shah, F. Blagojevic, D. S. Nikolopoulos, B. R.              Nikolopoulos, “Online power-performance adaptation of multithreaded
     de Supinski, and M. Schulz, “Prediction models for multi-dimensional            programs using hardware event-based prediction,” in Proceedings of
     power-performance optimization on many cores,” in Proceedings of the            the 20th Annual International Conference on Supercomputing, ser. ICS
     17th International Conference on Parallel Architectures and Compila-            ’06, 2006, pp. 157–166.
     tion Techniques, ser. PACT ’08, 2008, pp. 250–259.                         [62] P. E. Bailey, D. K. Lowenthal, V. Ravi, B. Rountree, M. Schulz,
[43] K. Singh, M. Curtis-Maury, S. A. McKee, F. Blagojević, D. S.                   and B. R. d. Supinski, “Adaptive configuration selection for power-
     Nikolopoulos, B. R. de Supinski, and M. Schulz, Comparing Scalability           constrained heterogeneous systems,” in 2014 43rd International Con-
     Prediction Strategies on an SMP of CMPs, 2010, pp. 143–155.                     ference on Parallel Processing, 2014, pp. 371–380.
[44] Z. Wang and M. F. O’Boyle, “Mapping parallelism to multi-cores:            [63] J. L. Berral, I. n. Goiri, R. Nou, F. Julià, J. Guitart, R. Gavaldà,
     A machine learning based approach,” in Proceedings of the 14th                  and J. Torres, “Towards energy-aware scheduling in data centers using
     ACM SIGPLAN Symposium on Principles and Practice of Parallel                    machine learning,” in Proceedings of the 1st International Conference
     Programming, ser. PPoPP ’09, 2009, pp. 75–84.                                   on Energy-Efficient Computing and Networking, ser. e-Energy ’10,
[45] Y. Kang, J. Hauswald, C. Gao, A. Rovinski, T. Mudge, J. Mars, and               2010, pp. 215–224.
     L. Tang, “Neurosurgeon: Collaborative intelligence between the cloud       [64] D. Del Vento, “Performance optimization on a supercomputer with
     and mobile edge,” in Proceedings of the Twenty-Second International             ctuning and the PGI compiler,” in Proceedings of the 2Nd International
     Conference on Architectural Support for Programming Languages and               Workshop on Adaptive Self-Tuning Computing Systems for the Exaflop
     Operating Systems, ser. ASPLOS ’17, 2017, pp. 615–629.                          Era, ser. EXADAPT ’12, 2012, pp. 12–20.

PROCEEDINGS OF IEEE                                                                                                                                          19



[65] P.-J. Micolet, A. Smith, and C. Dubach, “A machine learning approach        [87] C. Cummins, P. Petoumenos, Z. Wang, and H. Leather, “Synthesizing
     to mapping streaming workloads to dynamic multicore processors,” in              benchmarks for predictive modeling,” in Proceedings of the 2017
     ACM SIGPLAN Notices, vol. 51, no. 5, 2016, pp. 113–122.                          International Symposium on Code Generation and Optimization, ser.
[66] D. Grewe, Z. Wang, and M. F. P. O’Boyle, “Portable mapping of                    CGO ’17, 2017, pp. 86–99.
     data parallel programs to OpenCL for heterogeneous systems,” in             [88] J. MacQueen et al., “Some methods for classification and analysis of
     Proceedings of the 2013 IEEE/ACM International Symposium on Code                 multivariate observations,” 1967.
     Generation and Optimization (CGO), 2013, pp. 1–10.                          [89] T. Sherwood, E. Perelman, G. Hamerly, and B. Calder, “Automatically
[67] H. Yu and L. Rauchwerger, “Adaptive reduction parallelization tech-              characterizing large scale program behavior,” in Proceedings of the 10th
     niques,” in Proceedings of the 14th International Conference on                  International Conference on Architectural Support for Programming
     Supercomputing, ser. ICS ’00, 2000, pp. 66–77.                                   Languages and Operating Systems, ser. ASPLOS X, 2002, pp. 45–57.
[68] H. Leather, E. Bonilla, and M. O’Boyle, “Automatic feature generation       [90] Z. Wang and M. F. O’Boyle, “Partitioning streaming parallelism for
     for machine learning based optimizing compilation,” in Proceedings               multi-cores: A machine learning based approach,” in Proceedings
     of the 7th Annual IEEE/ACM International Symposium on Code                       of the 19th International Conference on Parallel Architectures and
     Generation and Optimization, ser. CGO ’09, 2009, pp. 81–91.                      Compilation Techniques, ser. PACT ’10, 2010, pp. 307–318.
[69] Z. Wang, D. Grewe, and M. F. P. O’boyle, “Automatic and portable            [91] M. Newman, Networks: An Introduction. New York, NY, USA: Oxford
     mapping of data parallel programs to opencl for GPU-Based heteroge-              University Press, Inc., 2010.
     neous systems,” ACM Trans. Archit. Code Optim., vol. 11, no. 4, pp.         [92] L. G. Martins, R. Nobre, A. C. Delbem, E. Marques, and
     42:1–42:26, 2014.                                                                J. a. M. Cardoso, “Exploration of compiler optimization sequences
[70] Y. Ding, J. Ansel, K. Veeramachaneni, X. Shen, U.-M. O’Reilly, and               using clustering-based selection,” in Proceedings of the 2014 SIG-
     S. Amarasinghe, “Autotuning algorithmic choice for input sensitivity,”           PLAN/SIGBED Conference on Languages, Compilers and Tools for
     in Proceedings of the 36th ACM SIGPLAN Conference on Program-                    Embedded Systems, ser. LCTES ’14, 2014, pp. 63–72.
     ming Language Design and Implementation, ser. PLDI ’15, 2015, pp.           [93] L. Eeckhout, H. Vandierendonck, and K. D. Bosschere, “Workload
     379–390.                                                                         design: selecting representative program-input pairs,” in Proceed-
[71] T. K. Ho, “Random decision forests,” in Proceedings of the Third Inter-          ings.International Conference on Parallel Architectures and Compi-
     national Conference on Document Analysis and Recognition (Volume                 lation Techniques, 2002, pp. 83–94.
     1) - Volume 1, ser. ICDAR ’95, 1995.                                        [94] Y. Chen, Y. Huang, L. Eeckhout, G. Fursin, L. Peng, O. Temam, and
[72] T. G. Dietterich, “Ensemble methods in machine learning,” in Proceed-            C. Wu, “Evaluating iterative optimization across 1000 datasets,” in
     ings of the First International Workshop on Multiple Classifier Systems,         Proceedings of the 31st ACM SIGPLAN Conference on Programming
     ser. MCS ’00, 2000, pp. 1–15.                                                    Language Design and Implementation, ser. PLDI ’10, 2010, pp. 448–
[73] P. Lokuciejewski, F. Gedikli, P. Marwedel, and K. Morik, “Automatic              459.
     WCET reduction by machine learning based heuristics for function            [95] A. H. Ashouri, G. Mariani, G. Palermo, and C. Silvano, “A bayesian
     inlining,” in 3rd Workshop on Statistical and Machine Learning Ap-               network approach for compiler auto-tuning for embedded processors,”
     proaches to Architectures and Compilation (SMART), 2009, pp. 1–15.               in Embedded Systems for Real-time Multimedia (ESTIMedia), 2014
[74] S. Benedict, R. S. Rejitha, P. Gschwandtner, R. Prodan, and                      IEEE 12th Symposium on. IEEE, 2014, pp. 90–97.
     T. Fahringer, “Energy prediction of openmp applications using random        [96] A. Phansalkar, A. Joshi, and L. K. John, “Analysis of redundancy
     forest modeling approach,” in 2015 IEEE International Parallel and               and application balance in the spec cpu2006 benchmark suite,” in
     Distributed Processing Symposium Workshop, 2015, pp. 1251–1260.                  Proceedings of the 34th Annual International Symposium on Computer
[75] R. Rejitha, S. Benedict, S. A. Alex, and S. Infanto, “Energy predic-             Architecture, ser. ISCA ’07, 2007, pp. 412–423.
     tion of cuda application instances using dynamic regression models,”        [97] P. Vincent, H. Larochelle, Y. Bengio, and P.-A. Manzagol, “Extracting
     Computing, pp. 1–26, 2017.                                                       and composing robust features with denoising autoencoders,” in Pro-
[76] C. Cummins, P. Petoumenos, Z. Wang, and H. Leather, “End-to-end                  ceedings of the 25th International Conference on Machine Learning,
     deep learning of optimization heuristics,” in The 26th International             ser. ICML ’08, 2008, pp. 1096–1103.
     Conference on Parallel Architectures and Compilation Techniques             [98] X. Gu, H. Zhang, D. Zhang, and S. Kim, “Deep API Learning.”
     (PACT), ser. PACT ’17, 2017.                                                [99] B. Singer and M. Veloso, “Learning to construct fast signal processing
[77] Z. Wang, G. Tournavitis, B. Franke, and M. F. O’boyle, “Integrat-                implementations,” Journal of Machine Learning Research, vol. 3, pp.
     ing profile-driven parallelism detection and machine-learning-based              887–919, 2002.
     mapping,” ACM Transactions on Architecture and Code Optimization           [100] X. Li, M. J. Garzaran, and D. Padua, “Optimizing sorting with genetic
     (TACO), vol. 11, no. 1, p. 2, 2014.                                              algorithms,” in Proceedings of the International Symposium on Code
[78] B. Taylor, V. S. Marco, and Z. Wang, “Adaptive optimization for                  Generation and Optimization, ser. CGO ’05, 2005, pp. 99–110.
     OpenCL programs on embedded heterogeneous systems,” in The 18th            [101] J. Ansel, C. Chan, Y. L. Wong, M. Olszewski, Q. Zhao, A. Edel-
     Annual ACM SIGPLAN / SIGBED Conference on Languages, Compil-                     man, and S. Amarasinghe, “Petabricks: A language and compiler for
     ers, and Tools for Embedded Systems, ser. LCETS ’17, 2017.                       algorithmic choice,” in ACM SIGPLAN Conference on Programming
[79] P. J. Joseph, K. Vaswani, and M. J. Thazhuthaveetil, “A predictive per-          Language Design and Implementation, ser. PLDI ’09, 2009.
     formance model for superscalar processors,” in Proceedings of the 39th     [102] M. Harman, W. B. Langdon, Y. Jia, D. R. White, A. Arcuri, and J. A.
     Annual IEEE/ACM International Symposium on Microarchitecture, ser.               Clark, “The gismoe challenge: Constructing the pareto program surface
     MICRO 39, 2006, pp. 161–170.                                                     using genetic programming to find better programs (keynote paper),”
[80] A. Ganapathi, K. Datta, A. Fox, and D. Patterson, “A case for machine            in Proceedings of the 27th IEEE/ACM International Conference on
     learning to optimize multicore performance,” in Proceedings of the               Automated Software Engineering, ser. ASE 2012, 2012, pp. 1–14.
     First USENIX Conference on Hot Topics in Parallelism, ser. HotPar’09,      [103] U. Garciarena and R. Santana, “Evolutionary optimization of compiler
     2009.                                                                            flag selection by learning and exploiting flags interactions,” in Proceed-
[81] E. Deniz and A. Sen, “Using machine learning techniques to detect                ings of the 2016 on Genetic and Evolutionary Computation Conference
     parallel patterns of multi-threaded applications,” International Journal         Companion, ser. GECCO ’16 Companion, 2016, pp. 1159–1166.
     of Parallel Programming, vol. 44, no. 4, pp. 867–900, 2016.                [104] M. Zuluaga, E. Bonilla, and N. Topham, “Predicting best design
[82] Y. LeCun, Y. Bengio, and G. Hinton, Deep Learning, 2015.                         trade-offs: A case study in processor customization,” in 2012 Design,
[83] A. Krizhevsky, I. Sutskever, and G. E. Hinton, “Imagenet classification          Automation Test in Europe Conference Exhibition (DATE), 2012, pp.
     with deep convolutional neural networks,” in Advances in Neural                  1030–1035.
     Information Processing Systems (NIPS), 2012.                               [105] M. R. Jantz and P. A. Kulkarni, “Exploiting phase inter-dependencies
[84] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image           for faster iterative compiler optimization phase order searches,” in
     recognition,” in The IEEE Conference on Computer Vision and Pattern              Compilers, Architecture and Synthesis for Embedded Systems (CASES),
     Recognition (CVPR), June 2016.                                                   2013 International Conference on. IEEE, 2013, pp. 1–10.
[85] H. Lee, Y. Largman, P. Pham, and A. Y. Ng, “Unsupervised feature           [106] E. Ipek, O. Mutlu, J. F. Martı́nez, and R. Caruana, “Self-optimizing
     learning for audio classification using convolutional deep belief net-           memory controllers: A reinforcement learning approach,” in Computer
     works,” in Proceedings of the 22Nd International Conference on Neural            Architecture, 2008. ISCA’08. 35th International Symposium on. IEEE,
     Information Processing Systems, ser. NIPS, 2009, pp. 1096–1104.                  2008, pp. 39–50.
[86] M. Allamanis and C. Sutton, “A Survey of Machine Learning for Big          [107] B. Porter, M. Grieves, R. Rodrigues Filho, and D. Leslie, “Rex:
     Code and Naturalness,” 2017.                                                     A development platform and online learning approach for runtime

PROCEEDINGS OF IEEE                                                                                                                                       20



      emergent software systems,” in Symposium on Operating Systems                    based optimization,” in Proceedings of the 2010 International Confer-
      Design and Implementation. USENIX, November 2016, pp. 333–348.                   ence on Compilers, Architectures and Synthesis for Embedded Systems,
[108] J. Rao, X. Bu, C.-Z. Xu, L. Wang, and G. Yin, “Vconf: A reinforcement            ser. CASES ’10, 2010, pp. 197–206.
      learning approach to virtual machines auto-configuration,” in Proceed-     [129] C. M. Bishop, Pattern Recognition and Machine Learning (Information
      ings of the 6th International Conference on Autonomic Computing, ser.            Science and Statistics). Secaucus, NJ, USA: Springer-Verlag New
      ICAC ’09, 2009, pp. 137–146.                                                     York, Inc., 2006.
[109] M. G. Lagoudakis and M. L. Littman, “Algorithm selection using re-         [130] K. Hoste, A. Phansalkar, L. Eeckhout, A. Georges, L. K. John, and
      inforcement learning,” in Proceedings of the Seventeenth International           K. De Bosschere, “Performance prediction based on inherent pro-
      Conference on Machine Learning, ser. ICML ’00, 2000, pp. 511–518.                gram similarity,” in Parallel Architectures and Compilation Techniques
[110] M. K. Emani and M. O’Boyle, “Change detection based parallelism                  (PACT), 2006 International Conference on. IEEE, 2006, pp. 114–122.
      mapping: Exploiting offline models and online adaptation,” in Lan-         [131] N. E. Rosenblum, B. P. Miller, and X. Zhu, “Extracting compiler
      guages and Compilers for Parallel Computing: 27th International                  provenance from program binaries,” in Proceedings of the 9th ACM
      Workshop (LCPC 2014), 2014, pp. 208–223.                                         SIGPLAN-SIGSOFT Workshop on Program Analysis for Software Tools
[111] Y. Li, “Deep reinforcement learning: An overview,” CoRR, vol. ab-                and Engineering, ser. PASTE ’10, 2010, pp. 21–28.
      s/1701.07274, 2017.                                                        [132] A. Bhattacharyya, G. Kwasniewski, and T. Hoefler, “Using compiler
[112] C. K. Williams and C. E. Rasmussen, “Gaussian processes for regres-              techniques to improve automatic performance modeling,” in 2015
      sion,” in Advances in neural information processing systems, 1996, pp.           International Conference on Parallel Architecture and Compilation
      514–520.                                                                         (PACT), 2015, pp. 468–479.
[113] C. E. Rasmussen and C. K. Williams, Gaussian processes for machine         [133] M. E. Taylor, K. E. Coons, B. Robatmili, B. A. Maher, D. Burger,
      learning. MIT press Cambridge, 2006, vol. 1.                                     and K. S. McKinley, “Evolving compiler heuristics to manage com-
[114] M. K. Emani and M. O’Boyle, “Celebrating diversity: A mixture of                 munication and contention,” in Proceedings of the Twenty-Fourth AAAI
      experts approach for runtime mapping in dynamic environments,” in                Conference on Artificial Intelligence, ser. AAAI’10, 2010, pp. 1690–
      Proceedings of the 36th ACM SIGPLAN Conference on Programming                    1693.
      Language Design and Implementation, ser. PLDI ’15, 2015, pp. 499–          [134] P. Ting, C. Tu, P. Chen, Y. Lo, and S. Cheng, “FEAST: An Au-
      508.                                                                             tomated Feature Selection Framework for Compilation Tasks,” arX-
[115] H. D. Nguyen and F. Chamroukhi, “An introduction to the practical                iv:1610.09543, 2016.
      and theoretical aspects of mixture-of-experts modeling,” arXiv preprint    [135] E. Park, C. Kartsaklis, and J. Cavazos, “Hercules: Strong patterns
      arXiv:1707.03538, 2017.                                                          towards more intelligent predictive modeling,” in 43rd International
[116] R. Polikar, “Ensemble based systems in decision making,” IEEE                    Conference on Parallel Processing, 2014, pp. 172–181.
      Circuits and systems magazine, vol. 6, no. 3, pp. 21–45.                   [136] K. Beyer, J. Goldstein, R. Ramakrishnan, and U. Shaft, “When is “n-
[117] L. Rokach, “Ensemble-based classifiers,” Artificial Intelligence Review,         earest neighbor” meaningful?” in International conference on database
      vol. 33, no. 1, pp. 1–39, 2010.                                                  theory. Springer, 1999, pp. 217–235.
[118] Y. Jiang, E. Z. Zhang, K. Tian, F. Mao, M. Gethers, X. Shen, and           [137] I. Fodor, “A survey of dimension reduction techniques,” Lawrence
      Y. Gao, “Exploiting statistical correlations for proactive prediction            Livermore National Laboratory, Tech. Rep., 2002.
      of program behaviors,” in Proceedings of the 8th Annual IEEE/ACM
                                                                                 [138] J. Thomson, M. F. O’Boyle, G. Fursin, and B. Franke, “Reducing
      International Symposium on Code Generation and Optimization, ser.
                                                                                       training time in a one-shot machine learning-based compiler.” in LCPC,
      CGO ’10, 2010, pp. 248–256.
                                                                                       vol. 5898. Springer, 2009, pp. 399–407.
[119] V. S. Marco, B. Taylor, B. Porter, and Z. Wang, “Improving spark
                                                                                 [139] Y. Bengio, “Learning deep architectures for ai,” Found. Trends Mach.
      application throughput via memory aware task co-location: A mixture
                                                                                       Learn., vol. 2, no. 1, pp. 1–127, 2009.
      of experts approach,” in ACM/IFIP/USENIX Middleware conference,
      2017.                                                                      [140] L. Deng, M. L. Seltzer, D. Yu, A. Acero, A.-r. Mohamed, and
[120] B. Singer and M. M. Veloso, “Learning to predict performance from                G. Hinton, “Binary coding of speech spectrograms using a deep auto-
      formula modeling and training data,” in Proceedings of the Seventeenth           encoder,” in Eleventh Annual Conference of the International Speech
      International Conference on Machine Learning, ser. ICML ’00, 2000,               Communication Association, 2010.
      pp. 887–894.                                                               [141] L. Mou, G. Li, L. Zhang, T. Wang, and Z. Jin, “Convolutional Neural
[121] E. Park, J. Cavazos, and M. A. Alvarez, “Using graph-based program               Networks over Tree Structures for Programming Language Processing,”
      characterization for predictive modeling,” in Proceedings of the Tenth           2013.
      International Symposium on Code Generation and Optimization, ser.          [142] M. White, M. Tufano, C. Vendome, and D. Poshyvanyk, “Deep
      CGO ’12, 2012, pp. 196–206.                                                      Learning Code Fragments for Code Clone Detection,” in ASE ’16
[122] A. M. Malik, “Spatial based feature generation for machine learning              (31st IEEE/ACM International Conference on Automated Software
      based optimization compilation,” in 2010 Ninth International Confer-             Engineering), 2016, pp. 87–98.
      ence on Machine Learning and Applications, 2010, pp. 925–930.              [143] M. White, M. Tufano, M. Martı́nez, M. Monperrus, and D. Poshyvanyk,
[123] M. Burtscher, R. Nasre, and K. Pingali, “A quantitative study of                 “Sorting and Transforming Program Repair Ingredients via Deep
      irregular programs on GPUs,” in Workload Characterization (IISWC),               Learning Code Similarities,” 2017.
      2012 IEEE International Symposium on, 2012, pp. 141–151.                   [144] L. Almagor, K. D. Cooper, A. Grosul, T. J. Harvey, S. W. Reeves,
[124] S. Browne, J. Dongarra, N. Garner, G. Ho, and P. Mucci, “A portable              D. Subramanian, L. Torczon, and T. Waterman, “Finding effective
      programming interface for performance evaluation on modern pro-                  compilation sequences,” in Proceedings of the 2004 ACM SIG-
      cessors,” The international journal of high performance computing                PLAN/SIGBED Conference on Languages, Compilers, and Tools for
      applications, vol. 14, no. 3, pp. 189–204, 2000.                                 Embedded Systems, ser. LCTES ’04, 2004, pp. 231–239.
[125] T. Mytkowicz, A. Diwan, M. Hauswirth, and P. F. Sweeney, “Producing        [145] K. D. Cooper, A. Grosul, T. J. Harvey, S. Reeves, D. Subramanian,
      wrong data without doing anything obviously wrong!” in Proceedings               L. Torczon, and T. Waterman, “ACME: Adaptive compilation made
      of the 14th International Conference on Architectural Support for                efficient,” in Proceedings of the 2005 ACM SIGPLAN/SIGBED Con-
      Programming Languages and Operating Systems, ser. ASPLOS XIV,                    ference on Languages, Compilers, and Tools for Embedded Systems,
      2009, pp. 265–276.                                                               ser. LCTES ’05, 2005, pp. 69–77.
[126] J. Cavazos, C. Dubach, F. Agakov, E. Bonilla, M. F. P. O’Boyle,            [146] A. H. Ashouri, A. Bignoli, G. Palermo, C. Silvano, S. Kulkarni,
      G. Fursin, and O. Temam, “Automatic performance model construction               and J. Cavazos, “MiCOMP: Mitigating the compiler phase-ordering
      for the fast software exploration of new hardware designs,” in Proceed-          problem using optimization sub-sequences and machine learning,”
      ings of the 2006 International Conference on Compilers, Architecture             ACM Trans. Archit. Code Optim., vol. 14, no. 3, pp. 29:1–29:28, 2017.
      and Synthesis for Embedded Systems, ser. CASES ’06, 2006, pp. 24–          [147] K. D. Cooper, D. Subramanian, and L. Torczon, “Adaptive optimizing
      34.                                                                              compilers for the 21st century,” The Journal of Supercomputing,
[127] S. Khan, P. Xekalakis, J. Cavazos, and M. Cintra, “Using predic-                 vol. 23, no. 1, pp. 7–22, 2002.
      tivemodeling for cross-program design space exploration in multicore       [148] D. R. White, A. Arcuri, and J. A. Clark, “Evolutionary improvement of
      systems,” in Proceedings of the 16th International Conference on                 programs,” IEEE Transactions on Evolutionary Computation, vol. 15,
      Parallel Architecture and Compilation Techniques. IEEE Computer                  no. 4, pp. 515–538, 2011.
      Society, 2007, pp. 327–338.                                                [149] G. Fursin and O. Temam, “Collective optimization: A practical collab-
[128] M. Namolaru, A. Cohen, G. Fursin, A. Zaks, and A. Freund, “Practical             orative approach,” ACM Trans. Archit. Code Optim., vol. 7, no. 4, pp.
      aggregation of semantical program properties for machine learning                20:1–20:29, Dec. 2010.

PROCEEDINGS OF IEEE                                                                                                                                         21



[150] J. Kukunas, R. D. Cupper, and G. M. Kapfhammer, “A genetic                [169] L. Tang, J. Mars, W. Wang, T. Dey, and M. L. Soffa, “Reqos: Reactive
      algorithm to improve linux kernel performance on resource-constrained           static/dynamic compilation for qos in warehouse scale computers,” in
      devices,” in Proceedings of the 12th Annual Conference Companion on             Proceedings of the Eighteenth International Conference on Architec-
      Genetic and Evolutionary Computation, ser. GECCO ’10, 2010, pp.                 tural Support for Programming Languages and Operating Systems, ser.
      2095–2096.                                                                      ASPLOS ’13, 2013, pp. 89–100.
[151] L.-N. Pouchet, C. Bastoul, A. Cohen, and J. Cavazos, “Iterative opti-     [170] A. Matsunaga and J. A. B. Fortes, “On the use of machine learning
      mization in the polyhedral model: Part ii, multidimensional time,” in           to predict the time and resources consumed by applications,” in
      Proceedings of the 29th ACM SIGPLAN Conference on Programming                   Proceedings of the 2010 10th IEEE/ACM International Conference on
      Language Design and Implementation, ser. PLDI ’08, 2008, pp. 90–                Cluster, Cloud and Grid Computing, ser. CCGRID ’10, 2010, pp. 495–
      100.                                                                            504.
[152] K. Asanovic, R. Bodik, B. C. Catanzaro, J. J. Gebis, P. Husbands,         [171] S. Venkataraman, Z. Yang, M. J. Franklin, B. Recht, and I. Stoica,
      K. Keutzer, D. A. Patterson, W. L. Plishker, J. Shalf, S. W. Williams           “Ernest: Efficient performance prediction for large-scale advanced
      et al., “The landscape of parallel computing research: A view from              analytics.” in NSDI, 2016, pp. 363–378.
      berkeley,” Technical Report UCB/EECS-2006-183, University of Cal-         [172] S. Sankaran, “Predictive modeling based power estimation for em-
      ifornia, Berkeley, Tech. Rep., 2006.                                            bedded multicore systems,” in Proceedings of the ACM International
[153] Y. Zhang, M. Voss, and E. S. Rogers, “Runtime empirical selection of            Conference on Computing Frontiers, ser. CF ’16, 2016, pp. 370–375.
      loop schedulers on hyperthreaded smps,” in 19th IEEE International        [173] Y. Zhang, M. A. Laurenzano, J. Mars, and L. Tang, “Smite: Precise qos
      Parallel and Distributed Processing Symposium, ser. IPDPS ’05, 2005.            prediction on real-system smt processors to improve utilization in ware-
[154] D. Rughetti, P. D. Sanzo, B. Ciciani, and F. Quaglia, “Machine                  house scale computers,” in Proceedings of the 47th Annual IEEE/ACM
      learning-based self-adjusting concurrency in software transactional             International Symposium on Microarchitecture, ser. MICRO-47, 2014,
      memory systems,” in 2012 IEEE 20th International Symposium on                   pp. 406–418.
      Modeling, Analysis and Simulation of Computer and Telecommunica-          [174] V. Petrucci, M. A. Laurenzano, J. Doherty, Y. Zhang, D. Mosse,
      tion Systems, 2012, pp. 278–285.                                                J. Mars, and L. Tang, “Octopus-man: Qos-driven task management
[155] C. Delimitrou and C. Kozyrakis, “Quasar: Resource-efficient and qos-            for heterogeneous multicores in warehouse-scale computers,” in 2015
      aware cluster management,” in Proceedings of the 19th International             IEEE 21st International Symposium on High Performance Computer
      Conference on Architectural Support for Programming Languages and               Architecture (HPCA). IEEE, 2015, pp. 246–258.
      Operating Systems, ser. ASPLOS ’14, 2014, pp. 127–144.                    [175] N. J. Yadwadkar, B. Hariharan, J. E. Gonzalez, and R. Katz, “Multi-task
[156] X. Chen and S. Long, “Adaptive multi-versioning for openmp paral-               learning for straggler avoiding predictive job scheduling,” The Journal
      lelization via machine learning,” in 2009 15th International Conference         of Machine Learning Research, vol. 17, no. 1, pp. 3692–3728, 2016.
      on Parallel and Distributed Systems, ser. ICPADS ’09, 2009, pp. 907–      [176] Y. David and E. Yahav, “Tracelet-based code search in executables,” in
      912.                                                                            Proceedings of the 35th ACM SIGPLAN Conference on Programming
[157] M. Castro, L. F. W. Ges, C. P. Ribeiro, M. Cole, M. Cintra, and                 Language Design and Implementation, ser. PLDI ’14, 2014, pp. 349–
      J. F. Mhaut, “A machine learning-based approach for thread mapping              360.
      on transactional memory applications,” in 2011 18th International         [177] Y. David, N. Partush, and E. Yahav, “Statistical similarity of binaries,”
      Conference on High Performance Computing, 2011, pp. 1–10.                       in Proceedings of the 37th ACM SIGPLAN Conference on Program-
[158] C. Jung, S. Rus, B. P. Railing, N. Clark, and S. Pande, “Brainy:                ming Language Design and Implementation, ser. PLDI ’16, 2016, pp.
                                                                                      266–280.
      Effective selection of data structures,” in Proceedings of the 32Nd
      ACM SIGPLAN Conference on Programming Language Design and                 [178] E. Wong, T. Liu, and L. Tan, “Clocom: Mining existing source code for
                                                                                      automatic comment generation,” in Software Analysis, Evolution and
      Implementation, ser. PLDI ’11, 2011, pp. 86–97.
                                                                                      Reengineering (SANER), 2015 IEEE 22nd International Conference on,
[159] Z. Wang and M. F. P. O’boyle, “Using machine learning to partition
                                                                                      2015, pp. 380–389.
      streaming programs,” ACM Trans. Archit. Code Optim., vol. 10, no. 3,
                                                                                [179] J. Fowkes and C. Sutton, “Parameter-free probabilistic api mining
      pp. 20:1–20:25, 2013.
                                                                                      across github,” in Proceedings of the 2016 24th ACM SIGSOFT
[160] C. Chan, J. Ansel, Y. L. Wong, S. Amarasinghe, and A. Edelman,                  International Symposium on Foundations of Software Engineering, ser.
      “Autotuning multigrid with petabricks,” in ACM/IEEE Conference on               FSE 2016, 2016, pp. 254–265.
      Supercomputing, ser. SC ’09, 2009.                                        [180] A. T. Nguyen, M. Hilton, M. Codoban, H. A. Nguyen, L. Mast,
[161] M. Pacula, J. Ansel, S. Amarasinghe, and U.-M. O’Reilly, “Hyperpa-              E. Rademacher, T. N. Nguyen, and D. Dig, “Api code recommendation
      rameter tuning in bandit-based adaptive operator selection,” in Euro-           using statistical learning from fine-grained changes,” in Proceedings of
      pean Conference on the Applications of Evolutionary Computation, ser.           the 2016 24th ACM SIGSOFT International Symposium on Foundations
      EuroSys ’12, 2012.                                                              of Software Engineering, ser. FSE 2016, 2016, pp. 511–522.
[162] J. Ansel, M. Pacula, Y. L. Wong, C. Chan, M. Olszewski, U.-               [181] V. Raychev, P. Bielik, and M. Vechev, “Probabilistic model for code
      M. O’Reilly, and S. Amarasinghe, “Siblingrivalry: Online autotuning             with decision trees,” in Proceedings of the 2016 ACM SIGPLAN
      through local competitions,” in Proceedings of the 2012 International           International Conference on Object-Oriented Programming, Systems,
      Conference on Compilers, Architectures and Synthesis for Embedded               Languages, and Applications, ser. OOPSLA 2016, 2016, pp. 731–747.
      Systems, ser. CASES ’12, 2012, pp. 91–100.                                [182] B. Bichsel, V. Raychev, P. Tsankov, and M. Vechev, “Statistical
[163] J. Ren, L. Gao, H. Wang, and Z. Wang, “Optimise web browsing on                 deobfuscation of android applications,” in Proceedings of the 2016
      heterogeneous mobile platforms: a machine learning based approach,”             ACM SIGSAC Conference on Computer and Communications Security,
      in IEEE International Conference on Computer Communications (IN-                ser. CCS ’16, 2016, pp. 343–355.
      FOCOM), 2017, ser. INFOCOM 2017, 2017.                                    [183] P. Balaprakash, R. B. Gramacy, and S. M. Wild, “Active-learning-based
[164] Y. Zhu and V. J. Reddi, “High-performance and energy-efficient mobile           surrogate models for empirical performance tuning,” in Cluster Com-
      web browsing on big/little systems,” ser. HPCA ’13, 2013.                       puting (CLUSTER), 2013 IEEE International Conference on. IEEE,
[165] Z. Wang, M. F. P. O’Boyle, and M. K. Emani, “Smart, adaptive                    2013, pp. 1–8.
      mapping of parallelism in the presence of external workload,” in          [184] W. F. Ogilvie, P. Petoumenos, Z. Wang, and H. Leather, “Fast automatic
      Proceedings of the 2013 IEEE/ACM International Symposium on Code                heuristic construction using active learning,” in International Workshop
      Generation and Optimization (CGO), ser. CGO ’13, 2013, pp. 1–10.                on Languages and Compilers for Parallel Computing, 2014, pp. 146–
[166] D. Grewe, Z. Wang, and M. F. P. O’Boyle, “A workload-aware                      160.
      mapping approach for data-parallel programs,” in Proceedings of the       [185] M. Zuluaga, G. Sergent, A. Krause, and M. Püschel, “Active learn-
      6th International Conference on High Performance and Embedded                   ing for multi-objective optimization,” in International Conference on
      Architectures and Compilers, ser. HiPEAC ’11, 2011, pp. 117–126.                Machine Learning, 2013, pp. 462–470.
[167] D. Grewe, Z. Wang, and M. F. OBoyle, “OpenCL task partitioning            [186] W. F. Ogilvie, P. Petoumenos, Z. Wang, and H. Leather, “Minimizing
      in the presence of GPU contention,” in International Workshop on                the cost of iterative compilation with active learning,” in Proceedings
      Languages and Compilers for Parallel Computing. Springer, 2013,                 of the 2017 International Symposium on Code Generation and Opti-
      pp. 87–101.                                                                     mization, ser. CGO ’17, 2017, pp. 245–256.
[168] L. Tang, J. Mars, and M. L. Soffa, “Compiling for niceness: Mitigating    [187] A. Evaluation. About artifact evaluation. [Online]. Available:
      contention for qos in warehouse scale computers,” in Proceedings of the         http://www.artifact-eval.org/about.html
      Tenth International Symposium on Code Generation and Optimization,        [188] cTuning Foundation. Artifact evaluation for computer systems’
      ser. CGO ’12, 2012, pp. 1–12.                                                   research. [Online]. Available: http://ctuning.org/ae/
