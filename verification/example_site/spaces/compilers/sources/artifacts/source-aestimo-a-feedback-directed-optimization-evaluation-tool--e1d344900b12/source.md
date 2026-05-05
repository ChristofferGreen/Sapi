# Aestimo: A Feedback-Directed Optimization Evaluation Tool

|     | Aestimo: |     | A   | Feedback-Directed                            |             |     | Optimization       |     |     | Evaluation |     | Tool |     |     |
| --- | -------- | --- | --- | -------------------------------------------- | ----------- | --- | ------------------ | --- | --- | ---------- | --- | ---- | --- | --- |
|     |          |     |     |                                              | PaulBerube, |     | Jose· NelsonAmaral |     |     | (cid:3)    |     |      |     |     |
|     |          |     |     | Dept. ofComputingScience,UniversityofAlberta |             |     |                    |     |     |            |     |      |     |     |
Edmonton,Alberta,T6G2E8,Canada
|     |     | Abstract |     |     |     |     |     | instrumented        |                                       | binary |           | training | input |         |
| --- | --- | -------- | --- | --- | --- | --- | --- | ------------------- | ------------------------------------- | ------ | --------- | -------- | ----- | ------- |
|     |     |          |     |     |     |     |     | this                |                                       |        | is runona |          |       | to gen- |
|     |     |          |     |     |     |     |     | erateapro(cid:2)le. | Finally,theprogramisrecompiled,andthe |        |           |          |       |         |
Published studies that use feedback-directed optimiza- compiler reads the pro(cid:2)le and replaces its static estimates
tion (FDO) techniques use either a single input for both ofprogrambehaviorwiththevaluesrecordedinthepro(cid:2)le.
trainingand performanceevaluation, or a single inputfor ThetraininginputusedwithFDOisanimportantcom-
trainingandasingleinputforevaluation. Thusanimpor- ponentoftheFDOprocess.ThesuccessofFDOdependson
tantquestionisiftheFDOresultspublishedintheliterature theselectionoftraininginputsthatarerepresentativeofthe
aresensitivetothetrainingandtestinginputselection. majorityofcommonusesofanapplication. Itis therefore
Aestimoisanewevaluationtoolthatusesaworkloadof importanttodeterminethesigni(cid:2)canceoftraining-inputse-
inputs to evaluate the sensitivity of specific code transfor- lectiononcodetransformationsthatusepro(cid:2)leinformation,
mations to the choice of inputs in the training and testing bothintermsofthedecisionsmadeatcompiletime,andin
phases.Aestimousesoptimizationlogstoisolatetheeffects termsoftheperformanceoftheresultingbinaries. Aestimo
ofindividualcodetransformations. Itincorporatesmetrics isatooldevelopedtofacilitatetheseinvestigations.
| to determine | the | effect of | training | input selection |     | on indi- |     |         |          |     |            |     |            |        |
| ------------ | --- | --------- | -------- | --------------- | --- | -------- | --- | ------- | -------- | --- | ---------- | --- | ---------- | ------ |
|              |     |           |          |                 |     |          |     | Studies | that use | FDO | techniques | may | use either | a sin- |
vidualcompilerdecisions. gle input for both training and performanceevaluation, or
Besides describing the structure of Aestimo, this paper a single input for training and a single input for evalua-
presentsacasestudythatusesSPECCINT2000benchmark tion [5, 23, 17, 14, 7, 20, 9, 25]. Few studies have inves-
programs with the Open Research Compiler (ORC) to in- tigatedtheimpactofthetraininginputusedinFDOonthe
vestigatetheeffectoftraining/testinginputselectiononin-
|     |     |     |     |     |     |     |     | performance | of  | the resulting | binary, | or methods |     | to effec- |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------- | --- | ------------- | ------- | ---------- | --- | --------- |
liningandif-conversion. Theexperimentalresultsindicate tivelyselecttraininginputs.
that: (1) training input selection affects the compiler de- Animportantquestionremainsopen: Howimportantis
cisionsmadeforthesecodetransformation;(2)thechoice theselectionoftrainingdataforFDO?Theanswerto this
of training/testing inputs can have a significant impact on questionisnotconstantacrossall transformationsthatuse
measuredperformance.
pro(cid:2)leinformation.Therefore,amoreappropriatequestion
|     |     |     |     |     |     |     |     | is: How | sensitive | are individual |     | compiler | transformations |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------- | --------- | -------------- | --- | -------- | --------------- | --- |
totheselectionoftrainingdatausedwithFDO?
1.Introduction This large question should be decomposed into more
|                   |     |              |     |        |            |     |     | manageableparts. |           | First,doestheselectionoftrainingdata |     |                |              |     |
| ----------------- | --- | ------------ | --- | ------ | ---------- | --- | --- | ---------------- | --------- | ------------------------------------ | --- | -------------- | ------------ | --- |
|                   |     |              |     |        |            |     |     | change the       | decisions | that                                 | are | made during    | compilation? |     |
| Feedback-directed |     | optimization |     | (FDO), | also known | as  |     |                  |           |                                      |     |                |              |     |
|                   |     |              |     |        |            |     |     | For example,     | does      | the selection                        |     | of a different | training     | in- |
pro(cid:2)le-guidedoptimization,mayenhancetheoptimization
|           |               |     |      |         |           |     |     | putchangewhichcallsitesareinlinedinaprogram? |               |     |                       |          |         | Ifthe     |
| --------- | ------------- | --- | ---- | ------- | --------- | --- | --- | -------------------------------------------- | ------------- | --- | --------------------- | -------- | ------- | --------- |
| decisions | in a compiler |     | [6]. | FDO can | be viewed | as  | a   |                                              |               |     |                       |          |         |           |
|           |               |     |      |         |           |     |     | answer to                                    | this question | is  | (cid:147)no,(cid:148) | then the | task is | complete: |
spectrumofperformance-enhancingtechniquesthatrelyon
Inputselectionisirrelevantforfeedback-directedoptimiza-
measurements of run-time program behavior [22]. In this tion. Therealityisthatoptimizationshavevariedmeasures
| paper a more | traditional |     | de(cid:2)nition | of FDO | is considered. |     |     |     |     |     |     |     |     |     |
| ------------ | ----------- | --- | --------------- | ------ | -------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ofinputselectionsensitivity.
WhenFDOisused,theprogramis(cid:2)rstcompiledwithad-
|     |     |     |     |     |     |     |     | Even | if different | decisions | are | made | by the | compiler, |
| --- | --- | --- | --- | --- | --- | --- | --- | ---- | ------------ | --------- | --- | ---- | ------ | --------- |
ditionalinstrumentationcodetorecordstatisticsaboutrun-
|                                                     |     |     |     |     |     |       |     | thesedifferencesmightnotbesigni(cid:2)cant. |     |        |             |                   | Thus,animpor- |     |
| --------------------------------------------------- | --- | --- | --- | --- | --- | ----- | --- | ------------------------------------------- | --- | ------ | ----------- | ----------------- | ------------- | --- |
| timeprogrambehaviorintoaprofileorfeedback(cid:2)le. |     |     |     |     |     | Then, |     |                                             |     |        |             |                   |               |     |
|                                                     |     |     |     |     |     |       |     | tant question                               | is: | Do the | differences | in transformation |               | de- |
cisionsresultindifferentlevelsofperformance?Iftraining
(cid:3) ThisresearchissupportedbyfellowshipsandgrantsfromtheNatural
SciencesandEngineeringResearchCouncilofCanada(NSERC),theIn- ondifferentinputsresultsindifferentlevelsofperformance,
formaticsCircleofResearchExcellence(iCORE),andtheCanadianFoun- theninputselectionforFDOisanimportantissue.
dationforinnovation(CFI).
1

| This | paper | presents | Aestimo, | a new | tool | to investigate |     |     |     |     |     |     |     |     |     |
| ---- | ----- | -------- | -------- | ----- | ---- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Compilation
FDOsystems,andreportsonaninitialexploratoryinvesti-
gationthatprovidesthefollowingcontributions:
|     |     |     |     |     |     |     |     |     | Binaries |     |     |     |     | Optimization |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | --- | --- | --- | ------------ | --- |
Logs
(cid:15) Introducesanexperimentalmethodologytoinvestigate
theimpactofinputselectiononindividualcodetrans-
| formations, |     | both in | terms | of compiler |     | decisions | and |     |     |     |     |     |     |     |     |
| ----------- | --- | ------- | ----- | ----------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Program
programperformance.
|     |     |     |     |     |     |     |     | Workload |     |     |     | Execution |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | --- | --- | --------- | --- | --- | --- |
(cid:15)
| Uses | a largeselection |     | of  | variedtraininginput |     |     | for the |     |     |     |     |     |     |     |     |
| ---- | ---------------- | --- | --- | ------------------- | --- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
SPECCINT2000benchmarkprogramstodemonstrate
| that | training | input | selection | does | impact | code | trans- |     |     |     |     |     |     |     |     |
| ---- | -------- | ----- | --------- | ---- | ------ | ---- | ------ | --- | --- | --- | --- | --- | --- | --- | --- |
Analysis
formationdecisionsandtheresultingprogramperfor-
mance.Additionally,thestudyshowsthattheselection
ofevaluationinputscansigni(cid:2)cantlyaltertheresultsof Performance Alignment
| performanceevaluation. |     |     |     |     |     |     |     |     | FDO vs Static |     |     |     | Difference |     |     |
| ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- | ------------- | --- | --- | --- | ---------- | --- | --- |
Resubstitution
| Material | in  | this paper | has | been previouslypresented |     |     | in  |     |     |     |     |     |     |     |     |
| -------- | --- | ---------- | --- | ------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Figure1.OverviewofAestimo
| an extendedform |     | in a | thesis | with the | same | title [2]. | Sec- |     |     |     |     |     |     |     |     |
| --------------- | --- | ---- | ------ | -------- | ---- | ---------- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
tion2providesanoverviewoftheexperimentalmethodol- of(cid:3)agsthatrefertothepro(cid:2)le(cid:2)le. Inthisstudy,the(cid:3)ags
ogy usedin this study, anddetails the operationandfunc- usedare-O3and-ipaforinlining,alongwithany(cid:3)agsfor
tions of Aestimo. Section 3 follows with a summary of de(cid:2)nesrequiredby theparticularSPEC benchmark. Only
theresultsfromanextensiveexperimentalstudyusingAes-
oneinstrumentedbinaryiscreatedforeachprogram.How-
timo, and presents a case study of inlining for bzip2 to ever,theremainingstepsinthe(cid:3)owdiagramareperformed
demonstrate the information provided by Aestimo. Sec- foreachoptimization/inputpairforeachprogram.
tion4presentssomerelatedwork,andSection5concludes.
WhenAestimoisinvestigatinganoptimizationP,itpro-
ducesbinariesthatonlyusepro(cid:2)le-guideddecisionsforP.
benchmarkB,
2.ExperimentalMethodology Foreach a trainingrunexecutesthe instru-
|     |     |     |     |     |     |     |     | mented | binary | on a | training | input. | Then, | B is compiled |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------ | ------ | ---- | -------- | ------ | ----- | ------------- | --- |
usingthegeneratedpro(cid:2)ledata,andanoptimizationlogL
| In order | to  | investigate | the | sensitivity |     | of individual |     |     |     |     |     |     |     |     |     |
| -------- | --- | ----------- | --- | ----------- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
feedback-directedcodeoptimizations,wecreatedAestimo1. is emittedforP. Thebinaryproducedat this pointis dis-
|     |     |     |     |     |     |     |     | carded. | AestimorecompilesB |     |     | staticallyusingLtoinstruct |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------------------ | --- | --- | -------------------------- | --- | --- | --- |
Aestimoisaperformanceevaluationtoolthatautomatesthe
|         |               |            |     |     |            |          |     | the compiler | to  | make | the same | decisions |     | for P as | it did |
| ------- | ------------- | ---------- | --- | --- | ---------- | -------- | --- | ------------ | --- | ---- | -------- | --------- | --- | -------- | ------ |
| process | of compiling, | executing, |     | and | evaluating | programs |     |              |     |      |          |           |     |          |        |
duringthefullpro(cid:2)le-guidedcompilation.Inthisway,opti-
onworkloadscomposedofseveralprograminputs.Figure1
mizationdecisionsbasedonpro(cid:2)leinformation(ratherthan
providesanoverviewofAestimo.
staticestimates)areusedonlyforP.Thebinariesproduced
bythis(cid:2)nalcompilationarereferredtoasFDObinaries.
| 2.1. Compilation |     |     | Process |     |     |     |     |         |                                |                         |     |     |          |             |        |
| ---------------- | --- | --- | ------- | --- | --- | --- | --- | ------- | ------------------------------ | ----------------------- | --- | --- | -------- | ----------- | ------ |
|                  |     |     |         |     |     |     |     | During  | the                            | (cid:2)nal compilation, |     | the | compiler | may         | not be |
|                  |     |     |         |     |     |     |     | able to | performeveryoptimizationlisted |                         |     |     | in       | L. Forexam- |        |
TheexperimentsperformedbyAestimorequiredthecre-
|     |     |     |     |     |     |     |     | ple,ifP | isifconversion,theremaybeafunctionthatisnot |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------------------------------------------- | --- | --- | --- | --- | --- | --- |
ationofalargenumberofbinaries.Aestimodistinguishesa Inthatcase,anyifcon-
inlinedwithoutpro(cid:2)leguidance.
program,whichisthealgorithmencodedinthesourcecode,
|     |     |     |     |     |     |     |     | versionlisted |     | inL fortheinlinedcodeinignored. |     |     |     |     | Onthe |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------- | --- | ------------------------------- | --- | --- | --- | --- | ----- |
binary,
froma whichis onecompiledinstance ofthe pro- otherhand,anyadditionaloptimizationsthatbecomeprof-
| gram. In                      | particular, | changingthe |     | traininginput            |     | used   | with   |                                |                                 |     |     |     |                     |            |     |
| ----------------------------- | ----------- | ----------- | --- | ------------------------ | --- | ------ | ------ | ------------------------------ | ------------------------------- | --- | --- | --- | ------------------- | ---------- | --- |
|                               |             |             |     |                          |     |        |        | itableduetoaforceddecisionwill |                                 |     |     |     | still beavailableto |            | the |
| FDOresultsinadifferentbinary. |             |             |     | A(cid:3)owdiagramforAes- |     |        |        |                                |                                 |     |     |     |                     |            |     |
|                               |             |             |     |                          |     |        |        | compiler.                      | Forexample,ifLforcesacallsiteto |     |     |     |                     | beinlined, |     |
| timo’s compilation            |             | process     | is  | presented                | in  | Figure | 2. The |                                |                                 |     |     |     |                     |            |     |
anystaticoptimizationsapplicabletotheinlinedcodewill
| bold boxes | indicate | (cid:147)(cid:2)nal | products(cid:148) |     | that are | subsequently |     |     |     |     |     |     |     |     |     |
| ---------- | -------- | ------------------- | ----------------- | --- | -------- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
stillbeapplied.Thus,Aestimoensuresthatanyopportunity
Aestimo.
used by Each benchmark program is compiled to apply P will result in the same decision as in the full
| statically | once | for each | optimization |     | being | studied | to cre- |                   |     |       |       |     |          |           |     |
| ---------- | ---- | -------- | ------------ | --- | ----- | ------- | ------- | ----------------- | --- | ----- | ----- | --- | -------- | --------- | --- |
|            |      |          |              |     |       |         |         | feedback-directed |     | case, | while | not | ignoring | cascading | ef- |
atethe(cid:147)static(cid:148)binary,andtocreatethestaticoptimization
fectsduetotheinterrelatednessofoptimizations.Nonethe-
logs. Thecompiler(cid:3)agsusedforthestaticcompilationare
less,theinteractionsbetweenoptimizationarecomplexand
| the same | as for | the pro(cid:2)led | case, | except | for | the omission |     |                         |     |            |                         |     |            |     |          |
| -------- | ------ | ----------------- | ----- | ------ | --- | ------------ | --- | ----------------------- | --- | ---------- | ----------------------- | --- | ---------- | --- | -------- |
|          |        |                   |       |        |     |              |     | generallyunpredicatble. |     |            | Therefore,              |     | the impact | of  | training |
|          |        |                   |       |        |     |              |     | data selection          |     | on program | performancediscoveredby |     |            |     | this     |
1AestimoisaLatinverbwhosemeaningissimilartothatoftheEnglish
verbevaluate. techniqueisonlyanestimate. Similarly,thecombinedim-

|     |     |     |     |     |     | Instrumenting |     | Instrumented |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------------- | --- | ------------ | --- | --- | --- | --- | --- | --- |
Source Code
|     |     |     |     |                   |     | Compilation |     | Binary  |     |     |               |     |     |     |
| --- | --- | --- | --- | ----------------- | --- | ----------- | --- | ------- | --- | --- | ------------- | --- | --- | --- |
|     |     |     |     | S t a t i c       |     |             |     |         |     |     | Tr a i n in g |     |     |     |
|     |     |     |     |                   |     | Profile     |     | Tr ai n | ing |     |               |     |     |     |
|     |     |     |     | Co m p i l a tion |     |             |     | R u     | n   |     | I n p u t     |     |     |     |
FDO
FDO Binary
Compilation
Optimization
Static Binary
Log
Optimization
Log
Static
|     |     |     |     |     |     | Compilation |     | Final Binary |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ----------- | --- | ------------ | --- | --- | --- | --- | --- | --- |
Figure2.Compilationprocess
pactofseveraloptimizationsis unlikelyto beequalto the piler that makes good use of pro(cid:2)le informationwill pro-
accumulatedimpactoftheoptimizationsmeasuredindivid- ducethefastestbinaryforagiveninputwhenresubstitution
Aestimo
| ually. |     |     |     |     |     |     | is used. |        | calculates |      | the rank  | of each | FDO    | binary |
| ------ | --- | --- | --- | --- | --- | --- | -------- | ------ | ---------- | ---- | --------- | ------- | ------ | ------ |
|        |     |     |     |     |     |     | on each  | input. | A rank     | of 1 | indicates | that a  | binary | is the |
2.2. Performance Evaluation fastestonaparticularinput. Thus,ifmoreaccuratepro(cid:2)le
|     |     |     |     |     |     |     | informationis |     | used | effectivelyduringFDO, |     |     | resubstitution |     |
| --- | --- | --- | --- | --- | --- | --- | ------------- | --- | ---- | --------------------- | --- | --- | -------------- | --- |
Afterthecompilationprocess,Aestimoexecuteseachof shouldproducebinarieswithlowranks.
theFDObinariesoneachoftheinputsintheprogramwork-
load (cid:2)ve times. Aestimo then analyzes the program run 2.3. Workload Selection
| times and | the optimization |     | logs | (cid:151) calculating | difference |     |     |     |     |     |     |     |     |     |
| --------- | ---------------- | --- | ---- | --------------------- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
andalignmentmetrics(cid:151)andreportstheresults. This study uses benchmarks, and datasets, from the
Aestimo uses two methodologies to report results: an CINT2000suite2
|            |      |       |           |     |               |     | SPEC      |      |            | [10]. | SPEC      | providesthreesets |           | of  |
| ---------- | ---- | ----- | --------- | --- | ------------- | --- | --------- | ---- | ---------- | ----- | --------- | ----------------- | --------- | --- |
| arithmetic | mean | and a | geometric | sum | of run times. | The |           |      |            |       |           |                   |           |     |
|            |      |       |           |     |               |     | inputsfor | each | benchmark: |       | test is a | verysmall         | inputthat |     |
arithmetic mean aggregates the raw run times for each of allow easy veri(cid:2)cation; train is a set of small or medium-
| the inputs | in the | workload | for | a given | binary and | reports |              |     |          |      |      |                 |     |        |
| ---------- | ------ | -------- | --- | ------- | ---------- | ------- | ------------ | --- | -------- | ---- | ---- | --------------- | --- | ------ |
|            |        |          |     |         |            |         | sized inputs | for | training | with | FDO; | ref (reference) |     | is the |
this sumas a percentfasterthanthe samemeasureforthe inputsetusedforperformanceevaluation. Thisstudyuses
| statically | optimized | binary. | The | geometric | sum is | similar, |     |     |     |     |     |     |     |     |
| ---------- | --------- | ------- | --- | --------- | ------ | -------- | --- | --- | --- | --- | --- | --- | --- | --- |
alltheSPECinputsplusadditionalinputschosentoberep-
| but, foreach | input, | it normalizesthe |     | runtimes | againstthe |     |     |     |     |     |     |     |     |     |
| ------------ | ------ | ---------------- | --- | -------- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
resentativeofthebenchmark’stypicalworkload.
statictimebeforeaggregating.Precisely,thegeometricsum Benchmarkauthorshavebeenconsulted,fortheirexpert
isde(cid:2)nedas:
knowledgeoftheprogram,toinformtheselectionofinputs.
|     |     |     |     | time (j) |     |     | ForGAPandcrafty,thebenchmarkauthorsprovidedad- |     |     |     |     |     |     |     |
| --- | --- | --- | --- | -------- | --- | --- | ---------------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
I
|     |     | G I = | X    |        |     |     |                                  |              |     |              |     | Inputsforbzip2and |        |      |
| --- | --- | ----- | ---- | ------ | --- | --- | -------------------------------- | ------------ | --- | ------------ | --- | ----------------- | ------ | ---- |
|     |     |       | time |        | (j) |     | ditionalinputsforuseinthisstudy. |              |     |              |     |                   |        |      |
|     |     |       | j2W  | static |     |     |                                  |              |     |              |     |                   |        |      |
|     |     |       |      |        |     |     | gzip                             | are selected | as  | a collection | of  | (cid:2)les in     | common | for- |
mats.InputsforparseraretakenfromtheProjectGuten-
| whereW | istheworkload,I |     | 2W  | isthetraininginputused |     |     |     |     |     |     |     |     |     |     |
| ------ | --------------- | --- | --- | ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
to create the binary, and time (j);j 2 W; is the time for bergebookscollection[4,13,24],web-pages[16],andthe
I
thebinarytrainedininputI torunontheinputj. Reuters-21578 text categorization test collection [19]. A
Aestimoalsocomparestheperformanceofthestatically syntheticgeneratoris usedto createprobleminstancesfor
optimizedbinarywiththe performanceof thefastest FDO MCF with parameters similar to the SPEC ref input. The
|                                         |     |     |     |     |          |     | placement | and | routing | tasks | of VPR | are considered |     | indi- |
| --------------------------------------- | --- | --- | --- | --- | -------- | --- | --------- | --- | ------- | ----- | ------ | -------------- | --- | ----- |
| binaryforeachinputintheprogramworkload. |     |     |     |     | Thismea- |     |           |     |         |       |        |                |     |       |
surerepresentsthebestcaseperformanceofFDOrecorded vidually,andusetheFPGAPlace-and-RouteChallenge[3]
| Aestimo, |     |         |           |       |         |     | problemsintheprogramworkload. |     |     |     | Intotal,116inputsare |     |     |     |
| -------- | --- | ------- | --------- | ----- | ------- | --- | ----------------------------- | --- | --- | --- | -------------------- | --- | --- | --- |
| by       | and | as such | providean | upper | boundon | FDO |                               |     |     |     |                      |     |     |     |
performancefortheinputsinW.
2Thefollowingbenchmarksareomittedbecausetheycouldnotbecom-
Resubstitutionisthepracticeofusingthesameinputfor
piledwiththeappropriate(cid:3)agsintheORC:perlbmk,vortex,twolf,
| boththetrainingandevaluationruns[18]. |     |     |     |     | Ideally,a | com- | GCCandeon |     |     |     |     |     |     |     |
| ------------------------------------- | --- | --- | --- | --- | --------- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- |

|     | void   | foo() |     |     |     |     |     |     |              |     |     | ~v ~v | ~v ~v |     |
| --- | ------ | ----- | --- | --- | --- | --- | --- | --- | ------------ | --- | --- | ----- | ----- | --- |
|     |        |       | fg  |     |     |     |     |     | callsite     |     |     | 1 2   | 3 4   |     |
|     |        |       |     |     |     |     |     |     | bar.foo      |     |     | 1 0   | 1 0   |     |
|     | void   | bar() | f   |     |     |     |     |     | main.foo     |     |     | 0 0   | 0 1   |     |
|     | foo(); |       |     |     |     |     |     |     | main.bar     |     |     | 0 1   | 1 1   |     |
|     | g      |       |     |     |     |     |     |     | main.bar.foo |     |     | 0 1   | 1 1   |     |
int main(int argc, char* argv[]) f Figure5.Logfilesconvertedtovectors
foo();
|     | bar(); |     |     |     |     |     |     |     |     |     | ~v  | ~v ~v | ~v  |     |
| --- | ------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | --- |
|     |        |     |     |     |     |     |     |     |     |     | 1   | 2 3   | 4   |     |
g
|     |     |     |     |     |     |     |     |     |     | ~v  | 0   | 3 2 | 4   |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
1
|     |                                   |     |     |     |     |     |     |     |     | ~v   |     | 0 1 | 1   |     |
| --- | --------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- |
|     | Figure3.Callsitesinasimpleprogram |     |     |     |     |     |     |     |     | 2    |     |     |     |     |
|     |                                   |     |     |     |     |     |     |     |     | ~v 3 |     | 0   | 2   |     |
|     |                                   |     |     |     |     |     |     |     |     | ~v   |     |     | 0   |     |
4
|     | callsite |     | log1 | log2 | log3 | log4 |     |     |     |     |     |     |     |     |
| --- | -------- | --- | ---- | ---- | ---- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
Table1.Valuesforthedifferencemetric
|     | bar.foo  |     | yes | no  | yes | no  |     |     |     |     |     |     |     |     |
| --- | -------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|     | main.foo |     | no  | no  | no  | yes |     |     |     |     |     |     |     |     |
main.bar no yes yes yes situationmayarisewhentheexistenceofonedecisionde-
main.bar.foo yes yes yes pendsonapreviousaf(cid:2)rmativedecision. Forexample,the
main.bar.foocallsitedoesnotexistinlog1inFigure4,soit
Figure4.Somepossibleinlininglogs
isassignedthedefaultvalueof0inthevectorsinFigure5.
|     |     |     |     |     |     |     |     | The | difference | metric | is  | de(cid:2)ned as | the squared | length |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------- | ------ | --- | --------------- | ----------- | ------ |
used,ofwhichonly32areprovidedbySPEC3.
|      |         |     |     |     |     |     |     | ofthedifferencevectorbetweentwologvectors~v |         |           |             |                 |              | i and~v j : |
| ---- | ------- | --- | --- | --- | --- | --- | --- | ------------------------------------------- | ------- | --------- | ----------- | --------------- | ------------ | ----------- |
|      |         |     |     |     |     |     |     | (cid:14)(~v ;~v                             | ) = j~v | (cid:0)~v | j2. Where   | decisions       | are recorded | in          |
| 2.4. | Metrics |     |     |     |     |     |     | i                                           | j       | i j       |             |                 |              |             |
|      |         |     |     |     |     |     |     |                                             |         |           | (cid:14)(~v | ;~v             |              |             |
|      |         |     |     |     |     |     |     | the vectors                                 | as      | 0s and    | 1s,         | i j ) is simply | the          | Hamming     |
|      |         |     |     |     |     |     |     | distance                                    | between | the       | vectors4.   | (cid:14) grows  | with the     | number      |
Does pro(cid:2)lingon differenttraining inputs result in dif- ofchoicesthatresultindifferentdecisionsinthetwologs.
| ferent | optimization |     | decisions | in the | compiler? | To  | address |     |     |     |     |     |     |     |
| ------ | ------------ | --- | --------- | ------ | --------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
Thus,(cid:14)indicateswhenadifferentselectionoftraininginput
| this | question, | we propose |     | methods | to quantitatively |     | mea- |         |                                   |     |     |     |                |     |
| ---- | --------- | ---------- | --- | ------- | ----------------- | --- | ---- | ------- | --------------------------------- | --- | --- | --- | -------------- | --- |
|      |           |            |     |         |                   |     |      | results | in differentoptimizationdecisions |     |     |     | duringcompila- |     |
surethedifferencesbetweensetsofoptimizationdecisions.
tion.DifferencevaluesfortheexamplearegiveninTable1.
| These | metrics | providea | concretemeasure |     |     | of the | extent to |     |          |     |             |      |                  |     |
| ----- | ------- | -------- | --------------- | --- | --- | ------ | --------- | --- | -------- | --- | ----------- | ---- | ---------------- | --- |
|       |         |          |                 |     |     |        |           | FDO | is based | on  | the premise | that | a representative | in- |
whichtheselectionoftrainingdatain(cid:3)uencesthewaythat putusedforpro(cid:2)lingre(cid:3)ectstheruntimebehaviorofother
aprogramisoptimizedbyacompiler.
|     |     |     |     |     |     |     |     | commoninputs. |     | Thus,optimizationlogsbasedonpro(cid:2)les |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------- | --- | ----------------------------------------- | --- | --- | --- | --- |
Duringthecompilationprocess,selectedcompilerdeci-
fromdifferentrepresentativetraininginputsshouldnotvary
| sionsarewritten |     | toa     | log(cid:2)le. | A particularinstancewhere |          |         |     |                     |     |                      |     |      |              |     |
| --------------- | --- | ------- | ------------- | ------------------------- | -------- | ------- | --- | ------------------- | --- | -------------------- | --- | ---- | ------------ | --- |
|                 |     |         |               |                           |          |         |     | signi(cid:2)cantly. |     | The differencemetric |     | does | not indicate | how |
| a decision      |     | is made | is a choice.  | The                       | selected | outcome | of  |                     |     |                      |     |      |              |     |
muchlogsagreewitheachotheracrosstheentiresetoflogs.
|     |     | decision. |     |     |     |     | foo |     |     |     |     |     |     |     |
| --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
the choice is a For example, at a callsite in Thealignmentmetricquanti(cid:2)esthelevelofagreementbe-
| a program, |     | the compiler |     | has a choice | about | inlining | foo, |     |     |     |     |     |     |     |
| ---------- | --- | ------------ | --- | ------------ | ----- | -------- | ---- | --- | --- | --- | --- | --- | --- | --- |
tweenoneoptimizationlogandthecollectivechoicesmade
| which | results | in a | yes or | no decision. | For | instance, | Fig- |     |     |     |     |     |     |     |
| ----- | ------- | ---- | ------ | ------------ | --- | --------- | ---- | --- | --- | --- | --- | --- | --- | --- |
acrossthelogsfromalltheinputsforaprogram.
ure3 shows the callsites ofa simple program. Threepos- Aestimo combined total
|                                     |              |                |     |     |          |             |     |                    | (cid:2)rst | calculates | the                              |                 | vector | for a     |
| ----------------------------------- | ------------ | -------------- | --- | --- | -------- | ----------- | --- | ------------------ | ---------- | ---------- | -------------------------------- | --------------- | ------ | --------- |
| sible                               | inlininglogs | arepresentedin |     |     | Figure4. | Thenotation |     |                    | T~         |            | T~                               |                 |        |           |
|                                     |              |                |     |     |          |             |     | set oflogs:        |            | =          | ~v .                             | is a measurethe | of     | agreement |
| caller.calleeisusedtonamecallsites. |              |                |     |     |          |             |     |                    |            | Pi         | i                                |                 |        |           |
|                                     |              |                |     |     |          |             |     | betweenallthelogs. |            |            | Achoicethatfrequentlyresultsinan |                 |        |           |
Log(cid:2)lesrecordthecompiler’schoicesanddecisionsfor
|                                                      |     |     |     |     |     |     |     | af(cid:2)rmative | decision   |     | will have | a high          | value recorded | at its |
| ---------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | ---------------- | ---------- | --- | --------- | --------------- | -------------- | ------ |
| anoptimizationduringasinglecompilation.Allthelogsfor |     |     |     |     |     |     |     |                  | T~         |     |           |                 |                |        |
|                                                      |     |     |     |     |     |     |     | index            | in , while | a   | decision  | that is usually | decided        | non-   |
a given program and optimization are processed together. af(cid:2)rmatively will have a low value in T~ . In the example,
| Eachlogisconvertedintoavector.Eachvectoristhesame |           |               |           |               |            |            |                | T~  |     | 3]T. |     |     |     |     |
| ------------------------------------------------- | --------- | ------------- | --------- | ------------- | ---------- | ---------- | -------------- | --- | --- | ---- | --- | --- | --- | --- |
|                                                   |           |               |           |               |            |            |                | =[2 | 1 3 |      |     |     |     |     |
| l en g                                            | t h , w i | t h o n e e n | tr y fo r | e v e r y u n | i q u e ch | o i c e re | co r d e d i n |     |     |      |     |     |     |     |
T~ (cid:1)~v
|     |     |     |     |     |     |     |     | Thealignmentofalog~v |     |     | i   | isde(cid:2)nedas: | (cid:11) i = | i   |
| --- | --- | --- | --- | --- | --- | --- | --- | -------------------- | --- | --- | --- | ----------------- | ------------ | --- |
t h e s e t o f l o g s . B y c o nv e nt i o n , a p o s i ti ve n o n - ze ro v a l u e i s T~ [j]
P j
recorded for an af(cid:2)rmative decision (choosing to perform (cid:11) is most usefully reported as a percentage, where the
sumoftheelementsofT~
the optimization), while a 0 is recorded in the vector for isusedasthedenominator.Recall
anon-af(cid:2)rmativedecision(choosingnottoperformanop- that the dot product of two vectors, ~x(cid:1)~y = j~xjj~yjcos((cid:18)),
timization). In the case where a choice is not present in where (cid:18) is the angle between the vectors. Therefore, (cid:11) is
T~
one or more logs, a default value of 0 is recorded. This related to the angle between a log and . Since (cid:11) i is the
3The additional inputs used in this study can be found at 4TheHammingdistanceisthenumberofbitsthataredifferentbetween
http://www.cs.ualberta.ca/(cid:24)berube/compiler/fdo/ twoequal-lengthbinaryvectors

T~
| accumulationoftheelement-wiseproductsof |     |     |     |     |     | and~v | , (cid:11) |     |  5  |     |     |     |     |     |
| --------------------------------------- | --- | --- | --- | --- | --- | ----- | ---------- | --- | --- | --- | --- | --- | --- | --- |
i
| is large | only if~v | has positive |     | values | (i.e., af(cid:2)rmative |     | de- |     |  4                           |     |     |     |     |     |
| -------- | --------- | ------------ | --- | ------ | ----------------------- | --- | --- | --- | ---------------------------- | --- | --- | --- | --- | --- |
|          |           | i            |     |        |                         |     |     |     | citatS naht retsaF % egraevA |     |     |     |     |     |
 3
| cisions) | at the | same indexes | as  | many | other | logs. If | a log |     |     |     |     |     |     |     |
| -------- | ------ | ------------ | --- | ---- | ----- | -------- | ----- | --- | --- | --- | --- | --- | --- | --- |
 2
| has no af(cid:2)rmative |     | decisions, |     | (cid:11) will | be 0. | On the | other |     |     |     |     |     |     |     |
| ----------------------- | --- | ---------- | --- | ------------- | ----- | ------ | ----- | --- | --- | --- | --- | --- | --- | --- |
 1
| hand, if                                                       | a log has | an af(cid:2)rmativedecision |     |     | for | every | choice |     |  0  |     |     |     |     |     |
| -------------------------------------------------------------- | --------- | --------------------------- | --- | --- | --- | ----- | ------ | --- | --- | --- | --- | --- | --- | --- |
| forwhichanylogrecordsaaf(cid:2)rmativedecisions,(cid:11)willbe |           |                             |     |     |     |       |        |     | -1  |     |     |     |     |     |
| 100%.Ahighalignmentscoredoesnotnecessarilyindicate             |           |                             |     |     |     |       |        |     | -2  |     |     |     |     |     |
-3
| moreeffeciveoptimization. |     |     | Somedecisionsmaybeharm- |     |     |     |     |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | ----------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
-4
| ful, while | manylogs | maymiss |     | an importantoptimization. |     |     |     |     |     |     |     |     |     |     |
| ---------- | -------- | ------- | --- | ------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
-5
Alowalignmentmayindicatethatalogcontainsbetterde-
Program
cisions that do not agree with most logs. In the example, 2pizb ytfarc pag pizg fcm resrap ecalp.rpv etuor.rpv egareva
| (cid:11) = 2 | = 22%, | (cid:11) = | 6 = | 67%, (cid:11) | = 8 | = 89%, | and |     |     |     |     |     |     |     |
| ------------ | ------ | ---------- | --- | ------------- | --- | ------ | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 9          |        | 2          | 9   |               | 3 9 |        |     |     |     |     |     |     |     |     |
7
(cid:11) 4 = =78%.
9
Itisimportanttonotethatthedifferenceandalignment
metricsdonotconsidertheperformanceofthebinariescor-
Figure6.AverageFDOifconversionperfor-
| responding | to  | the optimization |     | logs. | Consequently, |     | these |     |     |     |     |     |     |     |
| ---------- | --- | ---------------- | --- | ----- | ------------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- |
manceonItanium
| metricscores           | do  | notre(cid:3)ect | the                          | qualityof | a   | traininginput. |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --------------- | ---------------------------- | --------- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- |
| Furthermore,           | the | metrics         | only                         | measure   | the | similarity     | be- |     |     |     |     |     |     |     |
| tweenoptimizationlogs. |     |                 | Ifthedecisionsrecordedinmost |           |     |                |     |     |     |     |     |     |     |     |
 10
| logsarepoor,thena                                 |      | logwithhighdifferencescoresanda |             |                                    |           |          |        |                              |     |     |     |     |     |     |
| ------------------------------------------------- | ---- | ------------------------------- | ----------- | ---------------------------------- | --------- | -------- | ------ | ---------------------------- | --- | --- | --- | --- | --- | --- |
|                                                   |      |                                 |             |                                    |           |          |        | citatS naht retsaF % egraevA |  8  |     |     |     |     |     |
| low alignment                                     |      | may in                          | fact record | many                               | different | decision |        |                              |     |     |     |     |     |     |
| thatleadtoimprovedperformance.Ahighalignmentscore |      |                                 |             |                                    |           |          |        |                              |  6  |     |     |     |     |     |
| may indicate                                      | that | a log                           | contains    | a (cid:147)representative(cid:148) |           |          | set of |                              |  4  |     |     |     |     |     |
decisions,butthisdoesnotsuggestthatthesedecisionscor-
 2
respondtoafasterprogram.
 0
-2
| 2.5. Compiler |     | Infrastructure |     |     |     |     |     |     |     |     |     |     |     |     |
| ------------- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
-4
Program
Thisstudyusesversion2.1oftheOpenResearchCom-
|              |                  |                |       |          |               |         |      |     |     | 2pizb ytfarc pag | pizg | fcm resrap | ecalp.rpv | etuor.rpv egareva |
| ------------ | ---------------- | -------------- | ----- | -------- | ------------- | ------- | ---- | --- | --- | ---------------- | ---- | ---------- | --------- | ----------------- |
| piler (ORC), | an               | open-source    |       | compiler | based         | on the  | code |     |     |                  |      |            |           |                   |
| base of      | SGI’s            | Pro64 compiler |       | [1]. The | ORC           | focuses | on   |     |     |                  |      |            |           |                   |
| producing    | high-performance |                | code, | and      | is frequently |         | used |     |     |                  |      |            |           |                   |
forcompilerresearch.ORChasarichpro(cid:2)lertosupportits
FDO infrastructure. The IPF processor family is the only Figure 7. Average FDO inlining performance
onItanium
targetfortheORC.ORCcombinesamaturecodebasewith
state-of-the-artcompilertechnology.
|     |     |     |     |     |     |     |     | performanceby |     | 6% on | average | on the | Itanium. | The best- |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------- | --- | ----- | ------- | ------ | -------- | --------- |
3.EvaluatingFDO caseFDOinliningperformanceisslowerthanstaticinonly
|     |     |     |     |     |     |     |     | 6   | out of | 116 cases. Furthermore,the |     | fastest | FDO | inlining |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ------ | -------------------------- | --- | ------- | --- | -------- |
binariesaremorethan10%fasterthanstaticin41cases.
Thissectionsummarizestheresultsofacasestudythat
TheresultsfortheItanium2aredisappointing:ifcon-
usesAestimotostudytheifconversionandinliningtrans-
formationsintheORCcompiler,targetingtheItaniumand version almost always result in performance degradation
|     |     |     |     |     |     |     |     | and | inlining | producesmixedresults. |     | Extensive |     | results for |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | --------------------- | --- | --------- | --- | ----------- |
Itanium2processors[2].
theexperimentswithItanium2arepresentedin[2].
| Figure                               | 3 presents | the      | arithmetic-mean |      | performance |            | of  |      |      |        |          |     |       |     |
| ------------------------------------ | ---------- | -------- | --------------- | ---- | ----------- | ---------- | --- | ---- | ---- | ------ | -------- | --- | ----- | --- |
| the Itanium                          | FDO        | binaries | for             | each | benchmark   | program.   |     |      |      |        |          |     |       |     |
|                                      |            |          |                 |      |             |            |     | 3.1. | Case | Study: | Inlining | for | bzip2 |     |
| Theresultsaremixed,butonaverageFDOif |            |          |                 |      |             | conversion |     |      |      |        |          |     |       |     |
haslittleeffectonperformance.
On the other hand, the experimental results show that Tables 2 through 4 present difference and alignment
there are performance bene(cid:2)ts from feedback-directedin- scores for the FDO inlining logs of bzip2. Each pairing
lining. Furthermore, there are several cases where the se- oflogs resultsin a differencescore. Thesecondandthird
lectionoftraininginputhasasigni(cid:2)cantimpactonperfor- columns of the table report the mean and standard devia-
mance. Figure 3 shows the arithmetic-mean performance tion of the difference scores for the FDO log listed in the
ofFDOinliningoneachprogram. FDOinliningimproves (cid:2)rst columnpairedwith all theotherFDO logs. TheMax

| Input      | Mean   | StdDev | Max | Static | Alignment(%) |       |
| ---------- | ------ | ------ | --- | ------ | ------------ | ----- |
| combined   | 82.21  | 82.79  | 162 | 69     |              | 53.22 |
| compressed | 81.00  | 80.91  | 159 | 74     |              | 51.51 |
| docs       | 155.50 | 43.23  | 158 | 203    |              | 5.89  |
| gap        | 81.93  | 83.05  | 162 | 71     |              | 52.81 |
| graphic    | 80.93  | 81.97  | 160 | 75     |              | 52.53 |
| jpeg       | 159.21 | 44.25  | 162 | 207    |              | 6.23  |
| log        | 80.21  | 78.64  | 156 | 77     |              | 50.14 |
| mp3        | 157.36 | 43.74  | 160 | 205    |              | 6.10  |
| mpeg       | 159.21 | 44.25  | 162 | 207    |              | 6.23  |
| pdf        | 156.43 | 43.48  | 159 | 204    |              | 6.03  |
| program    | 82.36  | 82.66  | 162 | 73     |              | 53.01 |
random
|         | 80.00  | 79.83 | 157 | 76  |     | 51.30 |
| ------- | ------ | ----- | --- | --- | --- | ----- |
| reuters | 156.43 | 43.48 | 159 | 204 |     | 6.03  |
source
|                         | 81.00  | 82.90 | 161 | 72  |                | 53.15 |
| ----------------------- | ------ | ----- | --- | --- | -------------- | ----- |
| xml                     | 149.93 | 41.63 | 152 | 197 |                | 5.48  |
| Callsites(VectorLength) |        |       |     |     |                | 1464  |
| ChoiceswithYesConsensus |        |       |     |     | 0Full,0FDO     |       |
| ChoiceswithNoConsensus  |        |       |     |     | 779Full,835FDO |       |
| ChoiceswithoutConsensus |        |       |     |     | 685Full,629FDO |       |
Table2.Inliningmetricscoresforbzip2ontheItanium
| Input                   | Mean   | StdDev | Max | Static | Alignment |       |
| ----------------------- | ------ | ------ | --- | ------ | --------- | ----- |
| docs                    | 155.00 | 69.42  | 158 | 203    |           | 11.45 |
| jpeg                    | 158.33 | 70.89  | 162 | 207    |           | 12.12 |
| mp3                     | 156.67 | 70.16  | 160 | 205    |           | 11.85 |
| mpeg                    | 158.33 | 70.89  | 162 | 207    |           | 12.12 |
| pdf                     | 155.83 | 69.79  | 159 | 204    |           | 11.72 |
| reuters                 | 155.83 | 69.79  | 159 | 204    |           | 11.72 |
| xml                     | 150.00 | 67.10  | 152 | 197    |           | 10.65 |
| Callsites(VectorLength) |        |        |     |        |           | 1464  |
ChoiceswithYesConsensus
0Full,0FDO
| ChoiceswithNoConsensus  |     |     |     | 793Full,919FDO |     |     |
| ----------------------- | --- | --- | --- | -------------- | --- | --- |
| ChoiceswithoutConsensus |     |     |     | 671Full,545FDO |     |     |
Table3.Inliningmetricscoresforbzip2lowcutgroupontheItanium
| Input      | Mean | StdDev    | Max | Static | Alignment |       |
| ---------- | ---- | --------- | --- | ------ | --------- | ----- |
| combined   |      | 5.57 3.48 |     | 10     | 69        | 91.74 |
| compressed |      | 6.14 3.12 |     | 9      | 74        | 88.78 |
gap
|         |     | 5.00 3.08 |     | 8   | 71  | 91.03 |
| ------- | --- | --------- | --- | --- | --- | ----- |
| graphic |     | 5.00 2.74 |     | 7   | 75  | 90.55 |
log
|                         |     | 7.57 3.34 |     | 10  | 77           | 86.42 |
| ----------------------- | --- | --------- | --- | --- | ------------ | ----- |
| program                 |     | 5.86 3.49 |     | 9   | 73           | 91.38 |
| random                  |     | 6.14 2.79 |     | 7   | 76           | 88.43 |
| source                  |     | 4.14 2.38 |     | 7   | 72           | 91.62 |
| Callsites(VectorLength) |     |           |     |     |              | 183   |
| ChoiceswithYesConsensus |     |           |     |     | 58Full,69FDO |       |
| ChoiceswithNoConsensus  |     |           |     |     | 43Full,99FDO |       |
| ChoiceswithoutConsensus |     |           |     |     | 82Full,15FDO |       |
Table4.Inliningmetricscoresforbzip2highcutgroupontheItanium

columnreportsthemaximumdifferencebetweenalogand in this groupmust result in different hot sections of code.
any other FDO log. The Static column reports the differ- Thus, training on different inputs from the low cut group
encemetricwhena logis comparedto the static log. The results insigni(cid:2)cantlydifferentinliningdecisions, andare
(cid:2)nalcolumnofthetablereportsthealignmentscoreforthe thuswellsuitedtoourstudy.
Thestaticlogisincludedinthecombinedtotalvector
log.
 10
| whencalculatingalignmentscores. |     |     |     |     | Additionalrelevantin- |     |     |     |     |     |     |     |     |
| ------------------------------- | --- | --- | --- | --- | --------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
formationisrecordedinthelastfourrowsofeachtable.The
 8
citatS naht retsaF %
| numberof | callsites | listed | in  | the inlininglogs |     | indicates the |     |     |     |     |     |     |     |
| -------- | --------- | ------ | --- | ---------------- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- |
 6
| lengthofthevectorsusedtocalculatethemetrics. |     |                                    |                             |     |     | Choices |     |     |     |     |     |     |     |
| -------------------------------------------- | --- | ---------------------------------- | --------------------------- | --- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
| withYesorNo                                  |     | consensusarethosewherethesamedeci- |                             |     |     |         |     |  4  |     |     |     |     |     |
| sionismadeineverylog.                        |     |                                    | Fullconsensusisachievedwhen |     |     |         |     |  2  |     |     |     |     |     |
everylog,includingthestaticlog,isinagreementaboutthe
 0
decision.FDOconsensusignoresthestaticlog,andchecks
| for consensus | among |     | the FDO | logs | only. | The number of |     | -2  |     |     |     |     |     |
| ------------- | ----- | --- | ------- | ---- | ----- | ------------- | --- | --- | --- | --- | --- | --- | --- |
Training Dataset
choiceswithoutconsensusindicatesthemaximumpossible
|     |     |     |     |     |     |     |     | denibmoc | desserpmoc scod | pag cihparg gepj | gol 3pm gepm fdp | margorp modnar sretuer | ecruos citats lmx |
| --- | --- | --- | --- | --- | --- | --- | --- | -------- | --------------- | ---------------- | ---------------- | ---------------------- | ----------------- |
numberofchoiceswheretwologscoulddisagree.
Theconsensusvaluesforbzip2indicatethattheFDO
| inlining | logs are | not very | similar. | While | there | are a large |     |     |     |     |     |     |     |
| -------- | -------- | -------- | -------- | ----- | ----- | ----------- | --- | --- | --- | --- | --- | --- | --- |
numberofcallsiteswherethereisconsensustonotperform
|     |     |     |     |     |     |     | Figure |     | 8. FDO | Inlining | performance: |     | bzip2 |
| --- | --- | --- | --- | --- | --- | --- | ------ | --- | ------ | -------- | ------------ | --- | ----- |
inlining,therearenocallsitesthatareuniversallyinlined.
onItanium
| Aestimo       | can | perform | a cut | operation, | where     | the inputs |     |     |     |     |     |     |     |
| ------------- | --- | ------- | ----- | ---------- | --------- | ---------- | --- | --- | --- | --- | --- | --- | --- |
| in a workload | are | split   | into  | two groups | according | to their   |     |     |     |     |     |     |     |
alignmentscore. Ifaninputhasanalignmentscoregreater Figure8showstheperformanceimpact,usingthearith-
| thanthecutvalue,itis |              |     | assignedtothehighcut |            |     | group,but        |       |       |              |          |        | bzip2. |      |
| -------------------- | ------------ | --- | -------------------- | ---------- | --- | ---------------- | ----- | ----- | ------------ | -------- | ------ | ------ | ---- |
|                      |              |     |                      |            |     |                  | metic | mean, | of different | training | inputs | on     | Each |
| if it has            | an alignment |     | score                | lower than | the | cut value, it is |       |       |              |          |        |        |      |
inputintheworkloadisusedasatraininginputforonebi-
assigned to the low cut group. The static log is included nary.Thetraininginputusedislistedbeloweachbarinthe
| inbothgroups. |     | Afterthecutismade,themetricscoresare |     |     |     |     |        |                                    |     |     |     |     |           |
| ------------- | --- | ------------------------------------ | --- | --- | --- | --- | ------ | ---------------------------------- | --- | --- | --- | --- | --------- |
|               |     |                                      |     |     |     |     | graph. | Thebarsrepresenttheaverageruntimes |     |     |     |     | of5trials |
recalculatedforeachgroupseparately.Tables3and 4show on the entire workload, while the errorbars correspondto
theresultsofcuttingthelogsintotwogroups. theminimumandmaximumtimesfromthose5trials.
| The inputs | in  | the high | cut | group | (which | originally had |     |     |     |     |     |     |     |
| ---------- | --- | -------- | --- | ----- | ------ | -------------- | --- | --- | --- | --- | --- | --- | --- |
Despitethelargerangesofruntimesbetweentrials,Fig-
alignmentscoresgreaterthan45%)arequitesimilar.Inputs ure8showsthat,fortheItanium,trainingonthecombined
inthisgrouphavelowdifferencescoresandhighalignment
inputresultsinperformancegainsofabout8%,whiletrain-
valueswhentheyarecutfromtherestoftheinputs.Infact,
ingonxmlimprovesperformancebyonly2%.
thereareonly15callsiteswheretrainingondifferentinputs
| fromthisgroupresultsindifferentinliningdecisions. |            |       |            |             |            |               |                      |  16 |     |     |     |     |     |
| ------------------------------------------------- | ---------- | ----- | ---------- | ----------- | ---------- | ------------- | -------------------- | --- | --- | --- | --- | --- | --- |
| On the                                            | other      | hand, | the inputs | in          | the low    | cut group are |                      |  14 |     |     |     |     |     |
| signi(cid:2)cantly                                | different  |       | from       | each other. | Difference | values        | citatS naht retsaF % |  12 |     |     |     |     |     |
| are still                                         | very high, | and   | alignment  | scores      | are        | only slightly |                      |     |     |     |     |     |     |
 10
largerthanwhencalculatedusingtheentireworkload.Fur-
 8
thermore,thereisverylittleconsensusbetweenthelogsin
 6
| this group, | and | there | is still | no callsite | that | all logs agree |     |     |     |     |     |     |     |
| ----------- | --- | ----- | -------- | ----------- | ---- | -------------- | --- | --- | --- | --- | --- | --- | --- |
 4
| shouldbeinlined. |     | Thelowcutgrouplogscontainanorder |     |     |     |     |     |     |     |     |     |     |     |
| ---------------- | --- | -------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
 2
| of magnitude | more | callsites |     | than the | logs | of the high cut |     |     |     |     |     |     |     |
| ------------ | ---- | --------- | --- | -------- | ---- | --------------- | --- | --- | --- | --- | --- | --- | --- |
 0
group. Nonetheless,allFDOlogsonlycontainbetween82
Input Dataset (Fastest Training Input)
and93af(cid:2)rmativeinliningdecisions.Therefore,trainingon
|     |     |     |     |     |     |     |     | denibmoc | )denibmoc( desserpmoc )fdp( scod | )cihparg( pag )margorp( cihparg )denibmoc( gepj | )denibmoc( gol )ecruos( 3pm )denibmoc( gepm )denibmoc( fdp | )denibmoc( margorp )denibmoc( modnar )denibmoc( | sretuer )margorp( ecruos )denibmoc( lmx )ecruos( |
| --- | --- | --- | --- | --- | --- | --- | --- | -------- | -------------------------------- | ----------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------ |
inputsinthelowcutgroupmustresultintherepeatedinlin-
| ingofcallsites |     | in inlinedcode. |     | Eachcallsite |     | in an inlined |     |     |     |     |     |     |     |
| -------------- | --- | --------------- | --- | ------------ | --- | ------------- | --- | --- | --- | --- | --- | --- | --- |
calleecreatesanewcallsiteinthelogs.Inordertoincrease
|     |     |     |     |     |     |     | Figure |     | 9. Static | vs. | FDO Inlining |     | perfor- |
| --- | --- | --- | --- | --- | --- | --- | ------ | --- | --------- | --- | ------------ | --- | ------- |
thenumberofcallsitesinthelogsfrom183to1464,thissit-
uationmust haveoccurredveryfrequently. Since the logs mance: bzip2onItanium
inthelowcutgroupdonotagreeonwhichcallsitesshould
| be inlined, | they    | must          | represent | decisions | to  | inline differ-  |           |     |               |     |              |              |              |
| ----------- | ------- | ------------- | --------- | --------- | --- | --------------- | --------- | --- | ------------- | --- | ------------ | ------------ | ------------ |
|             |         |               |           |           |     |                 | Comparing |     | best-case     | FDO | performance  | to           | static opti- |
| ent call    | chains. | Consequently, |           | training  | on  | differentinputs |           |     |               |     |              |              |              |
|             |         |               |           |           |     |                 | mization  | is  | an optimistic |     | measure that | can identify | poten-       |

tial for FDO to improve performance. Figure 9 presents Itanium Itanium2
best-case FDO inlining for bzip2. Below the graph, in Input Rank Slower Rank Slower
|             |            |              |            |     |            |          |     |     |     | (%)  |     | (%)  |     |
| ----------- | ---------- | ------------ | ---------- | --- | ---------- | -------- | --- | --- | --- | ---- | --- | ---- | --- |
| parenthesis | beside the | names of the | evaluation |     | inputs, we |          |     |     |     |      |     |      |     |
|             |            |              |            |     |            | combined |     |     | 1   | 0.00 | 14  | 6.44 |     |
recordthetraininginputusedtocreatethefastestFDObi-
|     |     |     |     |     |     | compressed |     | 10  |     | 3.40 | 12  | 4.87 |     |
| --- | --- | --- | --- | --- | --- | ---------- | --- | --- | --- | ---- | --- | ---- | --- |
naryforeachevaluationinput.PerformanceontheItanium
|               |                |             |     |     |          | docs |     |     | 8   | 2.12 | 1   | 0.00 |     |
| ------------- | -------------- | ----------- | --- | --- | -------- | ---- | --- | --- | --- | ---- | --- | ---- | --- |
| is very good, | with a minimum | improvement |     | of  | about 4% |      |     |     |     |      |     |      |     |
|               |                |             |     |     |          | gap  |     |     | 4   | 0.53 | 1   | 0.00 |     |
andamaximumgainofabout13%.Theseresultshighlight
|     |     |     |     |     |     | graphic |     |     | 9   | 2.73 | 6   | 1.81 |     |
| --- | --- | --- | --- | --- | --- | ------- | --- | --- | --- | ---- | --- | ---- | --- |
thepotentialforFDOtoimproveperformance.
|                                             |     |     |     |     |     | jpeg |     |     | 7   | 3.63 | 9   | 1.63 |     |
| ------------------------------------------- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | ---- | --- | ---- | --- |
| Thebinarytrainedoncombinedisoftenthefastest |     |     |     |     | bi- |      |     |     |     |      |     |      |     |
|                                             |     |     |     |     |     | log  |     | 11  |     | 3.54 | 5   | 1.05 |     |
naryinFigure9.However,theperformanceofthisbinaryis
|                                                     |     |     |     |     |     | mp3  |     | 12  |     | 5.28 | 10  | 2.64 |     |
| --------------------------------------------------- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | ---- | --- | ---- | --- |
| notconsistentacrosstheinputswhereitachievesbestper- |     |     |     |     |     | mpeg |     |     |     |      |     |      |     |
|                                                     |     |     |     |     |     |      |     |     | 3   | 2.04 | 10  | 3.15 |     |
formance.Thisresultindicatesthatthecommonpracticeof
|     |     |     |     |     |     | pdf |     |     | 2   | 1.40 | 8   | 2.14 |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | --- | ---- | --- |
usingasingleinputfortheperformanceevaluationofcode program 5 0.59 4 1.59
transformationsisliabletoproduceunreliableresults. random 8 3.32 13 7.23
| InaneffectiveFDOsystem,moreaccuratefeedbackin- |     |     |     |     |     | reuters |     |     |     |      |     |      |     |
| ---------------------------------------------- | --- | --- | --- | --- | --- | ------- | --- | --- | --- | ---- | --- | ---- | --- |
|                                                |     |     |     |     |     |         |     | 11  |     | 4.80 | 5   | 0.82 |     |
formationshouldresultinafaster-runningbinary.Themost source 8 3.01 4 0.81
accurateinformationcanbeobtainedbyresubstitution,that xml 12 3.30 1 0.00
| is, using | the same input | for both | training | and evaluation. |     |     |     |     |     |     |     |     |     |
| --------- | -------------- | -------- | -------- | --------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Table5.Rankofresubstitutionbinariesforin-
Therefore,therankcalculatedbyAestimoforresubstitution
| binariesfromaneffectiveFDOsystemshouldbelow. |     |     |     |     |     | liningonbzip2 |     |     |     |     |     |     |     |
| -------------------------------------------- | --- | --- | --- | --- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- |
Unfortunately,theORCdoesnotappeartousefeedback
informationeffectivelyfortheprogramsandinputsusedin
|     |     |     |     |     |     | componentanalysis |     | (PCA) | of  | low-level | program |     | behavior |
| --- | --- | --- | --- | --- | --- | ----------------- | --- | ----- | --- | --------- | ------- | --- | -------- |
Table5listseachinputinthebzip2workload.
thisstudy. suchascachemissesandbranchmispredictions. They(cid:2)nd
Foreachinput,andforeachprocessor,therankoftheinlin- thatwhiledifferentinputstothesame programwereoften
| ingresubstitutionbinaryforthe |     | input | is  | listed, alongwith |     |           |           |     |         |       |           |        |        |
| ----------------------------- | --- | ----- | --- | ----------------- | --- | --------- | --------- | --- | ------- | ----- | --------- | ------ | ------ |
|                               |     |       |     |                   |     | clustered | together, | in  | several | cases | different | inputs | to the |
the performance difference between the resubstitution bi- sameprogramresultindatapointsinseparateclusters.This
| naryandtherank-1FDObinary. |     | Forinstance,the(cid:2)rstrow |     |     |     |     |     |     |     |     |     |     |     |
| -------------------------- | --- | ---------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:2)ndingsupportsourconclusionthattheinputtoaprogram
ofTable5showthatamongtheFDObinariesforbzip2on
doeshaveanimpactonprogrambehavior.
the14th
theItanium2, thebinarytrainedoncombinedis Phansalkar et al. survey the four generations of the
| fastest (of | 15) when evaluated | using | the | combined | input. |                |     |       |     |             |     |     |           |
| ----------- | ------------------ | ----- | --- | -------- | ------ | -------------- | --- | ----- | --- | ----------- | --- | --- | --------- |
|             |                    |       |     |          |        | SPEC benchmark |     | suite | and | investigate |     | how | the suite |
Furthermore, the binary trained on combined was 6.44% has evolved [21] using PCA on low-level, architecture-
slowerthanthefastestFDObinary.
|         |                 |            |      |           |      | independent | program |        | behaviors   | such | as  | instruction | mix,  |
| ------- | --------------- | ---------- | ---- | --------- | ---- | ----------- | ------- | ------ | ----------- | ---- | --- | ----------- | ----- |
| A lower | rank is usually | associated | with | a smaller | per- |             |         |        |             |      |     |             |       |
|         |                 |            |      |           |      | basic-block | size,   | branch | statistics, |      | and | locality.   | Their |
formance difference compared to the rank-1 binary for clustering suggests that several benchmarks in the SPEC
| bzip2. | Cases whereresubstitutionachievesgoodperfor- |     |     |     |     |                     |     |                                     |     |     |     |     |     |
| ------ | -------------------------------------------- | --- | --- | --- | --- | ------------------- | --- | ----------------------------------- | --- | --- | --- | --- | --- |
|        |                                              |     |     |     |     | suitesareredundant. |     | Basedontheiroverallcharacteristics, |     |     |     |     |     |
mancecomparedtotherank-1binaryaremorelikelytocor- bzip2 and gzip form the entirety of one cluster. How-
| respondtosituationswherebetterfeedbackinformationre- |          |                    |     |     |             |           |            | Aestimo |            |                    |     |                  |     |
| ---------------------------------------------------- | -------- | ------------------ | --- | --- | ----------- | --------- | ---------- | ------- | ---------- | ------------------ | --- | ---------------- | --- |
|                                                      |          |                    |     |     |             | ever, in  | our study, |         | (cid:2)nds | signi(cid:2)cantly |     | differentre-     |     |
| sults in better                                      | inlining | decision. However, |     | the | scarcity of |           |            |         |            |                    |     |                  |     |
|                                                      |          |                    |     |     |             | sults for | bzip2      | and     | gzip.      | Therefore,         |     | while clustering |     |
suchhighly-rankedresubstitutionbinariessuggeststhatthe basedonlow-levelprogrambehaviorsmayidentifyredun-
| FDO system | seldommakes | effectiveuse |     | ofmoreaccurate |     |     |     |     |     |     |     |     |     |
| ---------- | ----------- | ------------ | --- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
dancyforarchitecturalstudies,wecautioncompilerdesign-
feedbackinformationforeitherprocessor.Infact,theranks ersagainstomittingprogramsfromabenchmarksuitebased
| ofresubstitutionbinariesarefairlyevenlydistributedacross |     |     |     |     |     | onthistechnique. |     |     |     |     |     |     |     |
| -------------------------------------------------------- | --- | --- | --- | --- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- |
therangeofpossibleranks.Thisresultsuggeststhatthereis
|     |     |     |     |     |     | MinneSPEC |     | proposes | reduced |     | inputs | to the | SPEC |
| --- | --- | --- | --- | --- | --- | --------- | --- | -------- | ------- | --- | ------ | ------ | ---- |
norelationshipbetweenthequalityoffeedbackinformation CPU2000 benchmarks based on function-level execution
andtheperformanceoftheresultingbinary.
|     |     |     |     |     |     | pro(cid:2)les | and instruction |     | mix      | pro(cid:2)les | to reduce | simulation |          |
| --- | --- | --- | --- | --- | --- | ------------- | --------------- | --- | -------- | ------------- | --------- | ---------- | -------- |
|     |     |     |     |     |     | time for      | architecture    |     | research | [15].         | Eeckhout  | et         | al. ana- |
4.Related Work lyzeprogrambehavioronthereducedinputssuggestedby
|     |     |     |     |     |     | MinneSPEC[11]. |     | Theyusealargermixofbehaviormea- |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | -------------- | --- | ------------------------------- | --- | --- | --- | --- | --- |
suresthataremorecloselyrelatedtoprogramperformance
| 4.1. Input | Selection | and Benchmarking |     |     |     |                                          |       |      |       |               |     |     |          |
| ---------- | --------- | ---------------- | --- | --- | --- | ---------------------------------------- | ----- | ---- | ----- | ------------- | --- | --- | -------- |
|            |           |                  |     |     |     | thanthoseusedtocreatetheMinneSPECinputs. |       |      |       |               |     |     | PCAand   |
|            |           |                  |     |     |     | clustering                               | shows | that | while | the MinneSPEC |     | set | of large |
Eeckhoutetal.attemptto(cid:2)ndaminimalsetofrepresen-
|                 |            |                  |     |          |       | (lgred) inputs |     | remain | similar | to the | original | SPEC | inputs |
| --------------- | ---------- | ---------------- | --- | -------- | ----- | -------------- | --- | ------ | ------- | ------ | -------- | ---- | ------ |
| tative programs | and inputs | for architecture |     | research | [12]. |                |     |        |         |        |          |      |        |
fromwhichtheyarederived,themedium(mdred)andsmall
| They cluster | program-inputcombinations |     |     | using | principal- |     |     |     |     |     |     |     |     |
| ------------ | ------------------------- | --- | --- | ----- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |

(smred)inputsetsgenerallyleadtodissimilarprogrambe- dalealsoinvestigatesresubstitution,andconcludesthatpro-
havior. The MinneSPEC inputs, derived from SPEC in- (cid:2)le accuracy is not tightly coupled to performance gains.
putswiththeintentofmaintainingprogrambehavior,have We have also observed a general failure of resubstitution
limittedsuccessatachievingthisgoal. Therefore,it isnot to achieve the best performance. However, given the fre-
Aestimo
surprising that (cid:2)nds that alternate training inputs, quentlypoorperformanceofFDOcomparedtostaticopti-
which are intended to be different from the SPEC inputs, mization,webelievethatfurtherimprovementstotheFDO
alsoresultindifferentprogrambehavior,andconsequently systemmustbemadebeforewecanprovidea(cid:2)nalverdict
differentcompile-timedecisionsanddifferentlevelsofper- ontheusefulnessofperfectinformation.
formanceintheresultingFDObinaries.
CitroninvestigateatheuseoftheSPECbenchmarksby 4.3 Iterative Optimization
researchreportedincomputerarchitectureconferences[8]
| and (cid:2)nds | that | while commonly |     | used, the | suite | is seldom |           |             |     |        |      |          |          |
| -------------- | ---- | -------------- | --- | --------- | ----- | --------- | --------- | ----------- | --- | ------ | ---- | -------- | -------- |
|                |      |                |     |           |       |           | Iterative | compilation |     | can be | used | to giude | a search |
usedas intended. Theuseofonlyselectedprogramsfrom throughthe space ofpossible programtransformations. A
the benchmark suite is common, and can dramatically in- metric computed on the binary produced at one iteration
| (cid:3)ate reportedresults. |     | Our | resultscompoundthis |     |     | problem. |     |     |     |     |     |     |     |
| --------------------------- | --- | --- | ------------------- | --- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
guidesthecompilationofsubsequentiterations.
We have shown that the training input used with FDO as PanandEigenmannbreakaprogramintoregions,called
| well as | the testing | inputused |     | to evaluateperformancecan |     |     |                                 |     |     |     |                         |     |     |
| ------- | ----------- | --------- | --- | ------------------------- | --- | --- | ------------------------------- | --- | --- | --- | ----------------------- | --- | --- |
|         |             |           |     |                           |     |     | TuningSections(TS),andattemptto |     |     |     | (cid:2)ndanoptimalopti- |     |     |
signi(cid:2)cantly vary the observed performance impact of a mizationstrategyforeachTS[20]. TheirGCC-basedsys-
code transformation. The common practice of using only tem is able to improve performance on four SPEC 2000
| theinputssuppliedwiththeSPEC |     |     |     | benchmarksislikelyto |     |     |            |     |            |         |        |     |           |
| ---------------------------- | --- | --- | --- | -------------------- | --- | --- | ---------- | --- | ---------- | ------- | ------ | --- | --------- |
|                              |     |     |     |                      |     |     | benchmarks | by  | an average | of 26%. | Tuning | is  | giuded by |
further obscure the true impact of a technique when used the performanceofbinaries runonthe SPEC train inputs,
outsidethelab. whileevaluationusestheSPECrefinputs.Incontrasttoour
results,iftherefinputisresubstitutedinstead,muchlarger
4.2. Feedback-Directed Optimization performancegainsareobservedontwoofthebenchmarks.
|      |            |             |     |        |          |      | The performance |                | improvement | obtained                     |     | by this | approach         |
| ---- | ---------- | ----------- | --- | ------ | -------- | ---- | --------------- | -------------- | ----------- | ---------------------------- | --- | ------- | ---------------- |
|      |            |             |     |        |          |      | is often        | small compared |             | to the performancevariations |     |         | we               |
| Cohn | and Lowney | investigate |     | FDO in | Compaq’s | com- |                 |                |             |                              |     |         |                  |
|      |            |             |     |        |          |      | have seen       | between        | inputs,     | or compared                  |     | to the  | bene(cid:2)ts of |
pilertoolsfortheAlphaprocessorusingtheSPECCINT95
|     |     |     |     |     |     |     | the usual | FDO | inlining | used in our | study. | In 5 | of their 8 |
| --- | --- | --- | --- | --- | --- | --- | --------- | --- | -------- | ----------- | ------ | ---- | ---------- |
benchmarks[9].Theyreporttheperformanceimpactswhen
cases,thelargestperformancegainforabenchmarkisless
severalFDOoptimizationsareappliedindividually.Inpar-
|               |           |          |          |                     |     |     | than 4%, | and is | less than | 10% in | another | two | cases. Av- |
| ------------- | --------- | -------- | -------- | ------------------- | --- | --- | -------- | ------ | --------- | ------ | ------- | --- | ---------- |
| ticular, they | (cid:2)nd | that FDO | inlining | improvesperformance |     |     |          |        |           |        |         |     |            |
erageperformanceisin(cid:3)atedbytheremainingcase,where
| by up to | 45%, | and by | 10% | on average | over static | inlin- |               |          |     |             |     |           |       |
| -------- | ---- | ------ | --- | ---------- | ----------- | ------ | ------------- | -------- | --- | ----------- | --- | --------- | ----- |
|          |      |        |     |            |             |        | the technique | improves |     | performance | by  | more than | 170%. |
Aestimo
| ing. |     | (cid:2)nds much | smaller | gains for | FDO | inlining |     |     |     |     |     |     |     |
| ---- | --- | --------------- | ------- | --------- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
Therefore,wesuspectthatnon-iterativeFDOmayprovide
fromtheORC.Furthermore,unliketheCompaqcompiler,
amoreconsistentbene(cid:2)twhenappliedacrossalargercol-
FDOinliningwiththeORCdegradedperformanceinsome
lectionofprogramsandinputs.
| cases. However, |     | the differences |       | in compiler, | architecture, |     |     |     |     |     |     |     |     |
| --------------- | --- | --------------- | ----- | ------------ | ------------- | --- | --- | --- | --- | --- | --- | --- | --- |
| and benchmark   |     | programs        | makes | meaningful   | comparisons   |     |     |     |     |     |     |     |     |
5.Conclusion
betweentheperformanceresultsdif(cid:2)cult.
LangdalealsoinvestigatesthesensitivityofFDOtothe
trainingdataused[18]. Theprogramsandinputsfromthe Aestimo is a tool to investigate and evaluate individ-
SPEC95andSPEC2000benchmarksuitesareusedincon- ual optimizations in FDO systems. Aestimo introduces a
junction with Digital’s GEM compiler and the Alto link- methodologytoinvestigatecompilerdecisionsforindivid-
time optimizerfor the Alpha architecture. The study con- ualtransformationsandmeasurestheirperformanceconse-
cludes that there is a statistically signi(cid:2)cant difference in quences. Furthermore, the difference and alignment met-
performancewhen different training inputs are used. Our ricsquantitativelymeasurethedifferencesincompile-time
study expands on this work in two ways. First, we have decisions made based on different training inputs. Addi-
usedalargenumberofadditionalnon-SPECinputsforboth tionally, we select a large number of additional inputs for
trainingandevaluation. Second,wehaveinvestigatedindi- SPEC CINT2000benchmarkprogramsto create represen-
vidualoptimizationsthatbene(cid:2)tfromFDOratherthancon- tativeworkloadswithasubstantiallylargerdegreeofvaria-
sidering the entire FDO system as a whole. In our study, tionthanthesmallevaluationworkloadsprovidedbySPEC.
wehavealsoobservedvariationsinperformancewhendif- The results of an extensive experimental study using
ferent training inputs are used. However, the differences Aestimo are illustrated by a case study of inlining for the
in performance in our study are much larger, and can be bzip2benchmarkprogram.Selectingdifferenttrainingin-
observedwithoutresortingtostatistical techniques. Lang- putsresults insubstantiallydifferentinliningdecisionsfor

manyoftheinputsintheworkload. Furthermore,thereare [13] A. Einstein. Relativity : the Special and Gen-
signi(cid:2)cantperformancevariationsontheworkloaddepend- eral Theory. Project Gutenberg, January 2004.
http://www.gutenberg.org/etext/5001.
| ingwhichtraininginputisused. |     | UsingthefastestFDObi- |     |     |     |     |     |     |     |     |     |
| ---------------------------- | --- | --------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
nariesforeachinputrevealsthepotentialforFDOinlining [14] T. Kisuki, P. M. W. Knijnenburg, and M. F. P. O’Boyle.
Combinedselectionoftilesizesandunrollfactorsusingit-
tosubstantiallyimproveperformanceontheItanium.
|     |     |     |     |     |     | erativecompilation. | InIEEEPACT,pages237(cid:150)248,2000. |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------------------- | ------------------------------------- | --- | --- | --- | --- |
[15] A.KleinOsowskiandD.J.Lilja.MinneSPEC:AnewSPEC
Acknowledgments benchmark workload forsimulation-based computerarchi-
|     |     |     |     |     |     | tecture | research. In Computer |     | Architecture | Letters, | vol- |
| --- | --- | --- | --- | --- | --- | ------- | --------------------- | --- | ------------ | -------- | ---- |
ume1,June2002.
WeareverygratefultoBradleyCalderandDavidAugust
|     |     |     |     |     |     | [16] M. Krahulk | and J. | J. Holkins. |     | http://www.penny- |     |
| --- | --- | --- | --- | --- | --- | --------------- | ------ | ----------- | --- | ----------------- | --- |
fortheirmanydetailedcommentsthatimprovethewriting
|     |     |     |     |     |     | arcade.com/. | A popular | video-game | news | and webcomic |     |
| --- | --- | --- | --- | --- | --- | ------------ | --------- | ---------- | ---- | ------------ | --- |
inthispaper. website. Text from news posts from December 29, 2004
throughMay6,2005.
[17] P.Kulkarni,S.Hines,J.Hiser,D.Whalley,J.Davidson,and
References
|     |     |     |     |     |     | D. Jones.  | Fast searches | for effective |            | optimization | phase |
| --- | --- | --- | --- | --- | --- | ---------- | ------------- | ------------- | ---------- | ------------ | ----- |
|     |     |     |     |     |     | sequences. | In ACM        | SIGPLAN       | Conference | on Program-  |       |
TM
[1] Open research compiler for Itanium processor family. ming Language Design and Implementation, pages 165(cid:150)
| http://ipf-orc.sourceforge.net/.Latestrelease:ORC2.1,July |     |     |     |     |     | 198,2004. |     |     |     |     |     |
| --------------------------------------------------------- | --- | --- | --- | --- | --- | --------- | --- | --- | --- | --- | --- |
15,2003. [18] G.Langdale. TheEffectofProfile ChoiceandProfile Gath-
[2] P.Berube. Aestimo:Afeedback-directedoptimizationeval- eringMethodsonProfile-Driven OptimizationSystems.PhD
uationtool. Master’sthesis,UniversityofAlberta,October thesis,Carnegie-MellonUniversity,2004.
| 2005. |     |     |     |     |     | [19] D. | D. Lewis. |     | Reuters-21578 |     | text |
| ----- | --- | --- | --- | --- | --- | ------- | --------- | --- | ------------- | --- | ---- |
[3] V. Betz. FPGA place-and-route challenge. categorization test collection.
http://www.eecg.toronto.edu/ http://www.daviddlewis.com/resources/testcollections/
(cid:24)vaughn/challenge/challenge.html. reuters21578,May2004. Distribution1.0.
UniversityofToronto,
[20] Z.PanandR.Eigenmann.Ratingcompileroptimizationsfor
DepartmentofElectricalandComputerEngineering.
|     |     |     |     |     |     |     |     |     | ACM/IEEE | Conference |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | ---------- | --- |
[4] L. Carroll. Alice’s Adventures in Wonder- automatic performance tuning. In
land. Project Gutenberg, January 1991. on High Performance Networking and Computing (SC04),
http://www.gutenberg.org/etext/11. pages14(cid:150)23,November2004.
|                 |               |          |          |            |     | [21] A.Phansalkar,A.Joshi,L.Eeckhout,andL.K.John. |             |             |     |           | Mea- |
| --------------- | ------------- | -------- | -------- | ---------- | --- | ------------------------------------------------- | ----------- | ----------- | --- | --------- | ---- |
| [5] J. Cavazos, | J. Eliot, and | B. Moss. | Inducing | heuristics | to  |                                                   |             |             |     |           |      |
|                 |               |          |          |            |     | suring program                                    | similarity: | Experiments |     | with SPEC | CPU  |
decidewhethertoschedule.InPLDI’04:Proceedingsofthe
benchmarksuites.InIEEEInternationalSymposiumonPer-
ACMSIGPLAN2004conferenceonProgramminglanguage
designandimplementation,pages183(cid:150)194,NewYork,NY, formanceAnalysisofSystemsandSoftware(ISPASS),2005.
|     |     |     |     |     |     | [22] M. D. | Smith. Overcoming | the | challenges | to feedback- |     |
| --- | --- | --- | --- | --- | --- | ---------- | ----------------- | --- | ---------- | ------------ | --- |
USA,2004.ACMPress.
directedoptimization.InProceedingsoftheACMSIGPLAN
| [6] P.P.Chang,S.A.Mahlke,andW.meiW.Hwu. |     |     |     | Usingpro- |     |     |     |     |     |     |     |
| --------------------------------------- | --- | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
WorkshoponDynamicandAdaptiveCompilationandOp-
| (cid:2)le information | to assist | classic | code optimizations. |     | Soft- |     |     |     |     |     |     |
| --------------------- | --------- | ------- | ------------------- | --- | ----- | --- | --- | --- | --- | --- | --- |
timization(Dynamo’00),pages1(cid:150)11,Boston,MA,January
ware–PracticeandExperience,21(12):1301(cid:150)1321,1991.
2000.
| [7] K.ChowandY.Wu. | Feedback-directedselectionandchar- |     |     |     |     |     |     |     |     |     |     |
| ------------------ | ---------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
[23] M.Stephenson,S.Amarasinghe,M.Martin,andU.-M.O-
acterizationofcompileroptimizations.InMICRO32,Isreal,
|     |     |     |     |     |     | Reilly. | Meta optimization: | Improving |     | compiler heuristics |     |
| --- | --- | --- | --- | --- | --- | ------- | ------------------ | --------- | --- | ------------------- | --- |
Nov1999.
|               |                 |            |     |                 |     | with machine | learning. | In ACMSIGPLAN |     | Conference | on  |
| ------------- | --------------- | ---------- | --- | --------------- | --- | ------------ | --------- | ------------- | --- | ---------- | --- |
| [8] D.Citron. | MisSPECulation: | Partialand |     | misleadinguseof |     |              |           |               |     |            |     |
ProgrammingLanguageDesignandImplementation,pages
| SPEC | CPU2000 in computer | architecture |     | conferences. | In  |     |     |     |     |     |     |
| ---- | ------------------- | ------------ | --- | ------------ | --- | --- | --- | --- | --- | --- | --- |
77(cid:150)90,2003.
Proceedingsofthe30thAnnualInternationalSymposiumon [24] H. G. Wells. The War of the Worlds. Project Gutenberg,
ComputerArchitecture(ISCA’03),pages52(cid:150)59,2003.
|                                         |                   |          |          |       |           | October2004.             | http://www.gutenberg.org/etext/36. |                            |     |     |     |
| --------------------------------------- | ----------------- | -------- | -------- | ----- | --------- | ------------------------ | ---------------------------------- | -------------------------- | --- | --- | --- |
| [9] R. Cohn                             | and P. G. Lowney. | Feedback | directed |       | optimiza- |                          |                                    |                            |     |     |     |
|                                         |                   |          |          |       |           | [25] P.Zhaoand           | J.N.Amaral.                        | Toinlineornottoinline?     |     |     | En- |
| tioninCompaq’scompilationtoolsforAlpha. |                   |          |          | In2nd | ACM       |                          |                                    |                            |     |     |     |
|                                         |                   |          |          |       |           | hancedinliningdecisions. |                                    | InLanguagesandCompilersfor |     |     |     |
WorkshoponFeedback-DirectedOptimization,Haifa,Israel,
|               |     |     |     |     |     | ParallelComputing: | 16thInternationalWorkshop,October |     |     |     |     |
| ------------- | --- | --- | --- | --- | --- | ------------------ | --------------------------------- | --- | --- | --- | --- |
| November1999. |     |     |     |     |     | 2003.              |                                   |     |     |     |     |
[10] S.P.E.Corporation.SPEC:Thestandardperformanceeval-
| uationcorporation.                                 | http://www.spec.org/. |     |     |     |        |     |     |     |     |     |     |
| -------------------------------------------------- | --------------------- | --- | --- | --- | ------ | --- | --- | --- | --- | --- | --- |
| [11] L.Eeckhout,H.Vandierendonck,andK.D.Bosschere. |                       |     |     |     | De-    |     |     |     |     |     |     |
| signingcomputerarchitectureresearchworkloads.      |                       |     |     |     | InIEEE |     |     |     |     |     |     |
Computer,volume36,pages65(cid:150)71,February2003.
| [12] L. Eeckhout, | H. Vandierendonck, |     | and K. | D. Bosschere. |     |     |     |     |     |     |     |
| ----------------- | ------------------ | --- | ------ | ------------- | --- | --- | --- | --- | --- | --- | --- |
Quantifyingtheimpactofinputdatasetsonprogrambehav-
| ioranditsapplications. |     | JournalofInstruction-LevelParal- |     |     |     |     |     |     |     |     |     |
| ---------------------- | --- | -------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
lelism,5:1(cid:150)33,22003.
