# Ansor: Generating High-Performance Tensor Programs for Deep Learning

Ansor: Generating High-Performance
Tensor Programs for Deep Learning
Lianmin Zheng, UC Berkeley; Chengfan Jia, Minmin Sun, and Zhao Wu, Alibaba Group;
Cody Hao Yu, Amazon Web Services, Inc; Ameer Haj-Ali, UC Berkeley; Yida Wang,
Amazon Web Services; Jun Yang, Alibaba Group; Danyang Zhuo, UC Berkeley and
Duke University; Koushik Sen, Joseph E. Gonzalez, and Ion Stoica, UC Berkeley
https://www.usenix.org/conference/osdi20/presentation/zheng
This paper is included in the Proceedings of the
14th USENIX Symposium on Operating Systems
Design and Implementation
November 4–6, 2020
978-1-939133-19-9
Open access to the Proceedings of the
14th USENIX Symposium on Operating
Systems Design and Implementation
is sponsored by USENIX

Ansor: Generating High-Performance Tensor Programs for Deep Learning
LianminZheng1,ChengfanJia2,MinminSun2,ZhaoWu2,CodyHaoYu3 ,
AmeerHaj-Ali1,YidaWang3,JunYang2,DanyangZhuo1,4 ,
KoushikSen1,JosephE.Gonzalez1,IonStoica1
1 UCBerkeley,2AlibabaGroup,3AmazonWebServices,4 DukeUniversity
Abstract achieve high performance. However,these kernel libraries
require significant engineering effort to manually tune for
High-performancetensorprogramsarecrucialtoguarantee
eachhardwareplatformandoperator.Thesignificantmanual
efficientexecutionofdeepneuralnetworks.However,obtain-
effortrequiredtoproduceefficientoperatorimplementations
ing performant tensor programs for different operators on
foreachtargetacceleratorlimitsthedevelopmentandinnova-
varioushardwareplatformsisnotoriouslychallenging.Cur-
tionofnewoperators[7]andspecializedaccelerators[35].
rently,deeplearningsystemsrelyonvendor-providedkernel
GiventheimportanceofDNNs’performance,researchers
librariesorvarioussearchstrategiestogetperformanttensor
andindustrypractitionershaveturnedtosearch-basedcom-
programs.Theseapproacheseitherrequiresignificantengi-
pilation[2,11,32,49,59]forautomatedgenerationoftensor
neeringefforttodevelopplatform-specificoptimizationcode
programs,i.e.,low-levelimplementationsoftensoroperators.
or fall short of finding high-performance programs due to
Foranoperatorora(sub-)graphofmultipleoperators,users
restrictedsearchspaceandineffectiveexplorationstrategy.
definethecomputationinahigh-leveldeclarativelanguage
WepresentAnsor,atensorprogramgenerationframework
(§2),and the compilerthen searches forprograms tailored
fordeeplearningapplications.Comparedwithexistingsearch
towardsdifferenthardwareplatforms.
strategies,Ansorexploresmanymoreoptimizationcombina-
Tofindperformanttensorprograms,itisnecessaryfora
tionsbysamplingprogramsfromahierarchicalrepresentation
search-basedapproachtoexplorealargeenoughsearchspace
ofthesearchspace.Ansorthenfine-tunesthesampledpro-
tocoveralltheusefultensorprogramoptimizations.However,
gramswithevolutionarysearchandalearnedcostmodelto
existingapproachesfailtocapturemanyeffectiveoptimiza-
identifythebestprograms.Ansorcanfindhigh-performance
tion combinations, because they rely on either predefined
programsthatareoutsidethesearchspaceofexistingstate-of-
manually-writtentemplates(e.g.,TVM[12],FlexTensor[59])
the-artapproaches.Inaddition,Ansorutilizesataskscheduler
or aggressive pruning by evaluating incomplete programs
tosimultaneouslyoptimizemultiplesubgraphsindeepneural
(e.g.,Halideauto-scheduler[2]),whichpreventsthemfrom
networks.WeshowthatAnsorimprovestheexecutionperfor-
coveringacomprehensivesearchspace(§2).Therulesthey
manceofdeepneuralnetworksrelativetothestate-of-the-art
usetoconstructthesearchspacearealsolimited.
ontheIntelCPU,ARMCPU,andNVIDIAGPUbyupto
Inthispaper,weexploreanovelsearchstrategyforgener-
3.8 ,2.6 ,and1.7 ,respectively.
⇥ ⇥ ⇥ atinghigh-performancetensorprograms.Itcanautomatically
generatealargesearchspacewithcomprehensivecoverageof
1 Introduction optimizationsandgiveseverytensorprograminthespacea
chancetobechosen.Itthusenablestofindhigh-performance
Low-latencyexecutionofdeepneuralnetworks(DNN)plays programsthatexistingapproachesmiss.
a criticalrole in autonomous driving [14],augmentedreal- Realizingthisgoalfacesmultiplechallenges.First,itre-
ity[3],languagetranslation[15],andotherapplicationsof quiresautomaticallyconstructingalargesearchspacetocover
AI. DNNs can be expressed as a directed acyclic compu- asmanytensorprogramsaspossibleforagivencomputation
tational graph (DAG),in which nodes represent the opera- definition.Second,weneedtosearchefficientlywithoutcom-
tors (e.g.,convolution, matrix multiplication) and directed paringincompleteprogramsinthelargesearchspacethatcan
edgesrepresentthedependenciesbetweenoperators.Existing beordersofmagnitudelargerthanwhatexistingtemplates
deeplearningframeworks(e.g.,Tensorflow[1],PyTorch[39], cancover.Finally,whenoptimizinganentireDNNwithmany
MXNet[10])maptheoperatorsinDNNstovendor-provided subgraphs,weshouldrecognizeandprioritizethesubgraphs
kernel libraries (e.g., cuDNN [13], MKL-DNN [27]) to thatarecriticaltotheend-to-endperformance.
USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation 863

Tothisend,wedesignandimplementAnsor,aframework Matrix Multiplication ! ", % =∑ ) ( ", ) * ), %
for automated tensor program generation. Ansor utilizes a
C = compute((N, M), lambdai, j: sum(A[i, k]*B[k, j], [k]))
hierarchicalrepresentationtocoveralargesearchspace.This
representationdecoupleshigh-levelstructuresandlow-level Figure1:Thecomputationdefinitionofmatrixmultiplication.
details,enablingflexibleenumerationofhigh-levelstructures
To deliverportable performance of these operators on a
andefficientsamplingoflow-leveldetails.Thespaceiscon-
widerangeofhardwareplatformsinaproductiveway,multi-
structed automatically for a given computation definition.
plecompilertechniqueshavebeenintroduced(e.g.,TVM[11],
Ansorthensamplescompleteprogramsfromthesearchspace
Halide[41],TensorComprehensions[49]).Usersdefinethe
andfine-tunestheseprogramswithevolutionarysearchanda
computationinaformsimilartomathematicalexpressions
learnedcostmodel.TooptimizetheperformanceofDNNs
usingahigh-leveldeclarativelanguage,andthecompilergen-
withmultiplesubgraphs,Ansordynamicallyprioritizessub-
eratesoptimizedtensorprogramsaccordingtothedefinition.
graphsoftheDNNsthataremorelikelytoimprovetheend-
Figure1showsthecomputationdefinitionofmatrixmultipli-
to-endperformance.
cationintheTVMtensorexpressionlanguage.Usersmainly
WeevaluateAnsoronbothstandarddeeplearningbench- needtodefinetheshapesofthetensorsandhoweachelement
marksandemergingnewworkloadsagainstmanuallibraries intheoutputtensoriscomputed.
andstate-of-the-artsearch-basedframeworks.Experimentre-
However,automaticallygeneratinghigh-performanceten-
sultsshowthatAnsorimprovestheexecutionperformance
sorprograms from a high-level definition is extremely dif-
ofDNNsontheIntelCPU,ARMCPU,andNVIDIAGPU
ficult.Dependingonthearchitectureofthetargetplatform,
byupto3.8 ,2.6 ,and1.7 ,respectively.Formostcom-
thecompilerneedstosearchinanextremelylargeandcom-
⇥ ⇥ ⇥
putationdefinitions,thebestprogramfoundbyAnsorisout-
plicatedspacecontainingcombinatorialchoicesofoptimiza-
side the search space of existing search-based approaches.
tions(e.g.,tilestructure,tilesize,vectorization,paralleliza-
The results also show that,compared with existing search-
tion).Findinghigh-performanceprogramsrequiresthesearch
basedapproaches,Ansorsearchesmoreefficiently,generating
strategytocoveracomprehensivespaceandexploreiteffi-
higher-performance programs in a shortertime,despite its
ciently.Wedescribetworecentandeffectiveapproachesin
largersearchspace.Ansorcanmatchtheperformanceofa
thissectionandotherrelatedworkin§8.
state-of-the-artframeworkwithanorderofmagnitudeless
Template-guidedsearch.Intemplate-guidedsearch,the
searchtime.Besides,Ansorenablesautomaticextensionto
searchspaceisdefinedbymanualtemplates.AsshowninFig-
newoperatorsbyonlyrequiringtheirmathematicaldefinitions
ure2a,thecompiler(e.g.,TVM)requirestheusertomanually
withoutmanualtemplates.
writeatemplateforacomputationdefinition.Thetemplate
Insummary,thispapermakesthefollowingcontributions: definesthestructureofthetensorprogramswithsometunable
A mechanism to generate a large hierarchical search parameters(e.g.,tilesizeandunrollingfactor).Thecompiler
•
spaceoftensorprogramsforacomputationalgraph. thensearchesforthebestvaluesoftheseparametersforaspe-
cificinputshapeconfigurationandaspecifichardwaretarget.
Anevolutionarystrategywithalearnedcostmodelto
• Thisapproachhasachievedgoodperformanceoncommon
fine-tunetheperformanceoftensorprograms.
deeplearningoperators.However,developingtemplatesre-
A scheduling algorithm based on gradient descent to quiressubstantialeffort.Forexample,thecoderepositoryof
•
prioritizeimportantsubgraphswhenoptimizingtheend- TVMalreadycontainsmorethan15Klinesofcodeforthese
to-endperformanceofDNNs. templates.Thisnumbercontinuestogrowasnewoperators
Animplementationandcomprehensiveevaluationofthe andnewhardwareplatformsemerge.Besides,constructinga
•
Ansorsystemdemonstratingthattheabovetechniques qualitytemplaterequiresexpertiseinbothtensoroperators
outperformstate-of-the-artsystemsonavarietyofDNNs andhardware.Ittakesnon-trivialresearcheffort [32,55,59]
andhardwareplatforms. todevelopqualitytemplates.Despitethecomplexityoftem-
platedesign,manualtemplatesonlycoverlimitedprogram
structures because manually enumerating all optimization
2 Background choicesforalloperatorsisprohibitive. Thisapproachtypi-
callyrequiresdefiningonetemplateforeachoperator.Flex-
Thedeeplearningecosystemisembracingarapidlygrowing Tensor [59] proposes a general template to cover multiple
diversityofhardwareplatformsincludingCPUs,GPUs,FP- operators,butitstemplateisstilldesignedforsingleoperator
GAs,andASICs.InordertodeployDNNsontheseplatforms, granularity,which fails to include optimizations involving
high-performancetensorprogramsareneededfortheopera- multipleoperators(e.g.,operatorfusion).Thesearchspace
torsusedinDNNs.Therequiredoperatorsettypicallycon- ofoptimizingacomputationalgraphwithmultipleoperators
tainsamixtureofstandardoperators(e.g.,matmul,conv2d) shouldcontain differentwaystocomposetheoperators. A
andnoveloperatorsinventedbymachinelearningresearchers template-basedapproachfailstoachievethisbecauseitcan-
(e.g.,capsuleconv2d[23],dilatedconv2d[57]). notbreakdowntheirfixedtemplatesandre-composethem
864 14th USENIX Symposium on Operating Systems Design and Implementation USENIX Association

High-levelstructure generation
|     |     |     |     |     |     |     |     |     |     | for ... | ? for ... |     | for ... | ?   |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ------- | --------- | --- | ------- | --- | --- |
Parameter Serach Beam Search with Early Pruning for. ..... for. ..... ? for. .....
|     |     |     |     |     |     |     |     |     |     |     |     | for ... | for ... |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------- | --- | --- |
for ...
|     |     |     |     |     |     |     |     |     |     | for ... | for ... | ?   | for ... | ?   |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------- | --- | ------- | --- | --- |
Low-level detail sampling
| Fixed Manual Template |     |     |     |     |     | IncompleteProgram |     |     |     |     |     |     |     |     |     |
| --------------------- | --- | --- | --- | --- | --- | ----------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
CompletePrograms
for i.0 in range(512):
for i.0 in range( ? ): for j.0 in range(512): for i.0 in range(64):
for   j .0   i n ran g e (   ?   ) : for   j .0   i n r a n g e ( 6 4 ) :
|     |     |     |     |     |     | D[...] = | max(C[...], 0.0) |     |     |     |     | . . .r. |     |     |     |
| --- | --- | --- | --- | --- | --- | -------- | ---------------- | --- | --- | --- | --- | ------- | --- | --- | --- |
f or   k .0   in r a n g e (   ?  ): f or   k .0   in . a. n g e ( 5 12):
for i.1 in .r..ange( ?? ): How	to	build	th.e.	.next	statement	? for i.1 in range(8):
|     |     |     |     |     |     |     |     |     |     |     | for j.1 in | range(8): |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------- | --------- | --- | --- | --- |
for j.1 in range( ? ):
|     | C[...] +=  |             | A[...] * B[...] |     |     | Candidate	1 |     | Pruned |      |     | D[...] = ... |     |     |     |     |
| --- | ---------- | ----------- | --------------- | --- | --- | ----------- | --- | ------ | ---- | --- | ------------ | --- | --- | --- | --- |
|     | for i.2 in | range( ? ): |                 |     |     |             |     |        |      |     |              |     |     |     |     |
|     |            |             |                 |     |     | Candidate	2 |     |        | Kept |     |              |     |     |     |     |
for   j . 2   in r a n g e (  ?   ) : Evolutionary fine-tuning
|     | D [. | . . ]   = m | a x ( C[ . . . | ] , 0.0) |     | Candidate	3 |     |     | Kept |     |     |     |     |     |     |
| --- | ---- | ----------- | -------------- | -------- | --- | ----------- | --- | --- | ---- | --- | --- | --- | --- | --- | --- |
Better	Programs
|     |     |     |     |     |     | Candidate	4 |     | Pruned |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ----------- | --- | ------ | --- | --- | --- | --- | --- | --- | --- |
(a) Template-guided Search (b) Sequential Construction Based Search (c) Ansor’sHierarchical Approach
Figure2:Searchstrategycomparison.Thepseudo-codeshowstensorprogramswithloopnests.Thequestionmarksinorange
backgrounddenotelow-levelparameters.
duringthesearch.
Sequentialconstructionbasedsearch.Thisapproachde-
finesthesearchspacebydecomposingtheprogramconstruc-
| tion into | a fixed | sequence |     | of decisions. |     | The compilerthen |     |     |     |     |     |     |     |     |     |
| --------- | ------- | -------- | --- | ------------- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
usesanalgorithmsuchasbeamsearch[34]tosearchforgood
decisions(e.g.,Halideauto-scheduler[2]).Inthisapproach,
thecompilerconstructsatensorprogrambysequentiallyun- Figure3:Pairwisecomparisonaccuracyandtop-krecallcurve
onrandompartialprograms.Inbothsubfigures,highervalues
foldingallnodesinthecomputationalgraph.Foreachnode,
arebetter.
thecompilermakesafewdecisionsonhowtotransformit
(i.e.,
| into low-level |     | tensor | programs |     | deciding | computation |     |     |          |                |           |     |       |           |     |
| -------------- | --- | ------ | -------- | --- | -------- | ----------- | --- | --- | -------- | -------------- | --------- | --- | ----- | --------- | --- |
|                |     |        |          |     |          |             |     |     | score of | top-k programs | 1 (k=10). | As  | shown | in Figure | 3,  |
location,storagelocation,tilesize,etc.).Whenallnodesare
thetwocurvesstartfrom50%and0%respectively,meaning
unfolded,acompletetensorprogramisconstructed.Thisap-
thatrandomguesswithzeroinformationgives50%pairwise
proachusesasetofgeneralunfoldingrulesforeverynode,
|     |     |     |     |     |     |     |     |     | comparison | accuracy | and 0% top-k | recall. | The | two | curves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------- | -------- | ------------ | ------- | --- | --- | ------ |
soitcansearchautomaticallywithoutrequiringmanualtem-
plates. Becausethenumberofpossiblechoicesofeachde- increase quicklyas the programs become complete,which
meansthecostmodelperformsverywellforcompletepro-
cisionislarge,tomakethesequentialprocessfeasible,this
gramsbutfailstoaccuratelypredictthefinalperformanceof
approachkeepsonlytop-kcandidateprogramsaftereveryde-
incompleteprograms.(2)Thefixedorderofsequentialdeci-
cision.Thecompilerestimatesandcomparestheperformance
sionslimitsthedesignofthesearchspace.Forexample,some
ofcandidateprogramswithalearnedcostmodeltoselectthe
|     |     |     |     |     |     |     |     |     | optimization | needs | to addnewnodes |     | to the computational |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ------------ | ----- | -------------- | --- | -------------------- | --- | --- |
top-kcandidates;whileothercandidatesarepruned.During
|     |     |     |     |     |     |     |     |     | graph(e.g.,addingcachenodes,usingrfactor[46]). |     |     |     |     |     | The |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------------------------------------------- | --- | --- | --- | --- | --- | --- |
thesearch,thecandidateprogramsareincompletebecause
numberofdecisionsfordifferentprogramsbecomesdifferent.
onlypartofthecomputationalgraphisunfoldedoronlysome
Itishardtoaligntheincompleteprogramsforafaircompari-
ofthedecisionsaremade.Figure2bshowsthisprocess.
son.(3)Sequentialconstructionbasedsearchisnotscalable.
However,estimatingthefinalperformanceofincomplete
Enlargingthesearchspaceneedstoaddmoresequentialcon-
programsisdifficultinseveralrespects:(1)thecostmodel
structionsteps,which,however,leadstoaworseaccumulated
trainedoncompleteprogramscannotaccuratelypredictthe
error.
finalperformanceofincompleteprograms.Thecostmodel
|     |     |     |     |     |     |     |     |     | Ansor’s | hierarchical | approach | As  | shown | in Figure | 2c, |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------------ | -------- | --- | ----- | --------- | --- |
canonlybetrainedoncompleteprogramsbecauseweneed
Ansorisbackedbyahierarchicalsearchspacethatdecouples
| to compile | programs |     | and | measure | their | execution | time | to  |     |     |     |     |     |     |     |
| ---------- | -------- | --- | --- | ------- | ----- | --------- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
high-levelstructuresandlow-leveldetails.Ansorconstructs
getthelabelsfortraining.Directlyusingthismodeltocom-
|     |     |     |     |     |     |     |     |     | the search | space for | a computational |     | graph | automatically, |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------- | --------- | --------------- | --- | ----- | -------------- | --- |
parethefinalperformanceofincompleteprogramswillresult
eliminatingtheneedtomanuallydeveloptemplates.Ansor
| in pooraccuracy. |     | As  | a case | study,we | train | ourcostmodel |     |     |     |     |     |     |     |     |     |
| ---------------- | --- | --- | ------ | -------- | ----- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
thensamplescompleteprogramsfromthespaceandperforms
(§5.2)on20,000randomcompleteprogramsfromoursearch
fine-tuningoncompleteprograms,avoidingtheinaccuratees-
spaceandusethemodeltopredictthefinalperformanceof
timationofincompleteprograms.Figure2showsthekeydif-
incompleteprograms.Theincompleteprogramsareobtained
| by only | applying | a   | fraction | of loop | transformations |     | of  | the |                    |     |                                               |     |     |     |     |
| ------- | -------- | --- | -------- | ------- | --------------- | --- | --- | --- | ------------------ | --- | --------------------------------------------- | --- | --- | --- | --- |
|         |          |     |          |         |                 |     |     |     | 1recall@koftop-k=| | G   | \k P |,whereGisthesetoftop-kprogramsaccording |     |     |     |     |
completeprograms.Weusetworankingmetricsforevalua-
tothegroundtruthandPisthesetoftop-kprogramspredictedbythemodel.
tion:theaccuracyofpairwisecomparisonandtherecall@k
USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation    865

ferencebetweenAnsor’sapproachandexistingapproaches. Deep Learning Models
Partitioned subgraphs
3 DesignOverview TaskScheduler
Section 6
Subgraph 1 Subgraph 2 Subgraph 3 ·· ·
Ansorisanautomatedtensorprogramgenerationframework.
One subgraph
Figure4showstheoverallarchitectureofAnsor.Theinput
Program Sampler
ofAnsorisasetoftobeoptimizedDNNs. Ansorusesthe Section 4
Sketch Generation Random Annotation
operatorfusionalgorithmfromRelay[42]toconvertDNNs
from popularmodel formats (e.g.,ONNX [6],TensorFlow A batch of initial programs
PB) to partitioned small subgraphs. Ansor then generates Performance Tuner
Section 5
tensorprogramsforthesesubgraphs.Ansorhasthreemajor Evolutionary Search Learned Cost Model
components: (1) a program samplerthatconstructs a large A batch of opimizedprograms
search space and samples diverse programs from it; (2) a
Measurer
performancetunerthatfine-tunestheperformanceofsampled
Intel CPU ARM CPU NVIDIA GPU ·· ·
programs;(3)ataskschedulerthatallocatestimeresources
Execution time of programs
foroptimizingmultiplesubgraphsintheDNNs.
(training data for future iterations)
Program sampler. One key challenge Ansor has to ad-
Figure4:SystemOverview.Thegrayarrowsshowtheflow
dressisgeneratingalargesearchspaceforagivencomputa-
ofextractingsubgraphsfromdeeplearningmodelsandgen-
tionalgraph.Tocoverdiversetensorprogramswithvarious
eratingoptimizedprogramsforthem.Thegreenarrowsmean
high-levelstructuresandlow-leveldetails,Ansorutilizesa
themeasurerreturnsprofilingdatatoupdatethestatusofall
hierarchicalrepresentationofthesearchspacewithtwolev-
componentsinthesystem.
els:sketchandannotation(§4).Ansordefinesthehigh-level
structuresofprogramsassketchesandleavesbillionsoflow- Thetaskscheduler(§6)inAnsorusesaschedulingalgorithm
levelchoices(e.g.,tilesize,parallel,unrollannotations)as based on gradient descent to allocate resources to the sub-
annotations.ThisrepresentationallowsAnsortoenumerate graphsthataremorelikelytoimprovetheend-to-endDNN
high-levelstructuresflexiblyandsamplelow-leveldetailsef- performance.
ficiently. Ansorincludes a program samplerthatrandomly
samplesprogramsfromthespacetoprovidecomprehensive
coverageofthesearchspace. 4 ProgramSampling
Performance tuner. The performance ofrandomlysam-
pledprograms is notnecessarily good. The nextchallenge Thesearchspaceanalgorithmexploresdeterminesthebest
istofine-tunethem.Ansoremploysevolutionarysearchand programsitcanfind.Theconsideredsearchspacesinexisting
alearnedcostmodeltoperformfine-tuningiteratively(§5). approachesarelimitedbythefollowingfactors:(1)Manual
At each iteration,Ansoruses re-sampled new programs as enumeration(e.g.,TVM[12]).Itisimpracticaltomanually
well as good programs from previous iterations as the ini- enumerateallpossiblechoicesbytemplates,soexistingman-
tialpopulationtostarttheevolutionarysearch.Evolutionary ualtemplatesonlycoveralimitedsearchspaceheuristically.
searchfine-tunesprogramsbymutationandcrossoverwhich (2)Aggressiveearlypruning(e.g.,Halideauto-scheduler[2]).
perform out-of-order rewrite and address the limitation of Aggressiveearlypruningbasedonevaluatingincompletepro-
sequentialconstruction.Queryingthelearnedcostmodelis gramspreventsthesearchalgorithmfromexploringcertain
ordersofmagnitudefasterthanactualmeasurement,sowe regionsinthespace.
canevaluatethousandsofprogramsinseconds. Inthissection,weintroducetechniquestopushthebound-
Taskscheduler.Usingprogramsamplingandperformance aryoftheconsideredsearchspacebyaddressingtheabove
fine-tuningallowsAnsortofindhigh-performancetensorpro- limitations.Tosolve(1),weautomaticallyexpandthesearch
gramsforacomputationalgraph.Intuitively,treatingawhole spacebyrecursivelyapplyingasetofflexiblederivationrules.
DNNasasinglecomputationalgraphandgeneratingafull Toavoid(2),werandomlysamplecompleteprogramsinthe
tensorprogramforitcouldpotentiallyachievetheoptimal searchspace.Sincerandomsamplinggivesanequalchance
performance.This,however,isinefficientbecauseithasto to every pointto be sampled,oursearchalgorithm can po-
dealwiththeunnecessaryexponentialexplosionofthesearch tentiallyexploreeveryprogramintheconsideredspace.We
space.Typically,thecompilerpartitionsthelargecomputa- donotrelyonrandomsamplingtofindtheoptimalprogram,
tionalgraphofaDNNintoseveralsmallsubgraphs[11,42]. becauseeverysampledprogramislaterfined-tuned(§5).
This partition has a negligible effect on the performance Tosampleprogramsthatcancoveralargesearchspace,we
thanks to the layer-by-layer construction nature of DNNs. defineahierarchicalsearchspacewithtwolevels:sketchand
ThisbringsthefinalchallengeofAnsor:howtoallocatetime annotation.Wedefinethehigh-levelstructuresofprograms
resourceswhengeneratingprogramsformultiplesubgraphs. assketchesandleavebillionsoflow-levelchoices(e.g.,tile
866 14th USENIX Symposium on Operating Systems Design and Implementation USENIX Association

| No RuleName    |     |     | Condition              |     |     |     | Application         |     |     |     |     |
| -------------- | --- | --- | ---------------------- | --- | --- | --- | ------------------- | --- | --- | --- | --- |
| 1 Skip         |     |     | IsStrictInlinable(S,i) |     |     |     | S0=S;i0=i           | 1   |     |     |     |
|                |     |     | ¬                      |     |     |     |                     |    |     |     |     |
|                |     |     | IsStrictInlinable(S,i) |     |     |     | S0=Inline(S,i);i0=i |     |     |     |     |
| 2 AlwaysInline |     |     |                        |     |     |     |                     |     | 1   |     |     |

3 Multi-levelTiling HasDataReuse(S,i) S0=MultiLevelTiling(S,i);i0=i 1

4 Multi-levelTilingwithFusion HasDataReuse(S,i) HasFusibleConsumer(S,i) S0=FuseConsumer(MultiLevelTiling(S,i),i);i0=i 1
|     |     |     |     | ^   |     |     |     |     |     |     |    |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
5 AddCacheStage HasDataReuse(S,i) HasFusibleConsumer(S,i) S0=AddCacheWrite(S,i);i=i0
^¬
6 ReductionFactorization HasMoreReductionParallel(S,i) S0=AddRfactor(S,i);i0=i 1

| ... UserDefinedRule |     |     | ... |     |     |     | ... |     |     |     |     |
| ------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Table1:Derivationrulesusedtogeneratesketches.Theconditionrunsonthecurrentstates=(S,i).Theapplicationderivesthe
| nextstates | 0 =(S,i)fromthecurrentstates.Notethatsomefunction(e.g.,AddRfactor,FuseConsumer)canreturnmultiple 0 0 |     |     |     |     |     |     |     |     |     |     |
| ---------- | ---------------------------------------------------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
possiblevaluesofS.InthiscasewecollectallpossibleS,andreturnmultiplenextstatess forasingleinputstates.
|     | 0   |     |     |     | 0   |     |     |     | 0   |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
size,parallel,unrollannotations)asannotations.Atthetop decreases monotonically. A state becomes a terminal state
level, we generate sketches by recursively applying a few when i=0. During enumeration,multiple rules can be ap-
derivationrules.Atthebottomlevel,werandomlyannotate pliedtoonestatetogeneratemultiplesucceedingstates.One
thesesketchestogetcompleteprograms.Thisrepresentation rule can also generate multiple possible succeeding states.
summarizesafewbasicstructuresfrombillionsoflow-level Sowemaintainaqueuetostoreallintermediatestates.The
choices,enablingtheflexibleenumerationofhigh-levelstruc- processendswhenthequeueisempty. Alls.S interminal
turesandefficientsamplingoflow-leveldetails. statesformasketchlistattheendofthesketchgeneration.
WhileAnsorsupportsbothCPUandGPU,weexplainthe Thenumberofsketchesislessthan10foratypicalsubgraph.
samplingprocessforCPUsin§4.1and§4.2asanexample. Derivation rules. Table 1 lists derivation rules we used
WethendiscusshowtheprocessisdifferentforGPUin§4.3. for the CPU. We first provide the definition of the used
|     |     |     |     |     |     | predicates            | and then | describe  | the functionality | of each   | rule.  |
| --- | --- | --- | --- | --- | --- | --------------------- | -------- | --------- | ----------------- | --------- | ------ |
|     |     |     |     |     |     | IsStrictInliable(S,i) |          | indicates | if the node       | i in S is | a sim- |
4.1 SketchGeneration
|     |     |     |     |     |     | ple element-wise |     | operator | that can always | be inlined | (e.g., |
| --- | --- | --- | --- | --- | --- | ---------------- | --- | -------- | --------------- | ---------- | ------ |
AsshowninFigure4,theprogramsampleracceptspartitioned element-wise add,ReLU). HasDataReuse(S,i) indicates if
subgraphsasinput.ThefirstcolumninFigure5showstwo the node i in S is a compute-intensive operator and has
examplesoftheinput.Theinputhasthreeequivalentforms: plentiful intra-operator data reuse opportunity (e.g., mat-
|                  |                |     |               |       |      | mul, conv2d). | HasFusibleConsumer(S,i) |     |     | indicates | if the |
| ---------------- | -------------- | --- | ------------- | ----- | ---- | ------------- | ----------------------- | --- | --- | --------- | ------ |
| the mathematical | expression,the |     | corresponding | naive | pro- |               |                         |     |     |           |        |
gramobtainedbydirectlyexpandingtheloopindices,andthe node i in S has only one consumer j and node j can be
correspondingcomputationalgraph(directedacyclicgraph, fusedintonodei(e.g.,matmul+bias_add,conv2d+relu).
| orDAG). |     |     |     |     |     | HasMoreReductionParallel(S,i)indicatesifthenodeiinS |     |     |     |     |     |
| ------- | --- | --- | --- | --- | --- | --------------------------------------------------- | --- | --- | --- | --- | --- |
TogeneratesketchesforaDAGwithmultiplenodes,we haslittleparallelisminspacedimensionsbuthasampleparal-
lelismopportunityinreductiondimensions.(e.g.,computing
visitallthenodesinatopologicalorderandbuildthestructure
iteratively.Forcomputationnodesthatarecompute-intensive 2-normofamatrix,matmulC 2 2 =A 2 512 B 512 2 ).Weper-
|     |     |     |     |     |     |     |     |     | ⇥ ⇥ | · ⇥ |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
andhavealotofdatareuseopportunities(e.g.,conv2d,mat- formstaticanalysisonthecomputationdefinitionstogetthe
mul),webuildbasictileandfusionstructuresforthemasthe valuesforthesepredicates.Theanalysisisdoneautomatically
sketch.Forsimpleelement-wisenodes(e.g.,ReLU,element- byparsingtheread/writepatterninthemathematicalexpres-
sions.Next,weintroducethefunctionalityofeachderivation
| wiseadd),wecan | safelyinlinethem. |           | Notethatnewnodes |     |         |       |     |     |     |     |     |
| -------------- | ----------------- | --------- | ---------------- | --- | ------- | ----- | --- | --- | --- | --- | --- |
| (e.g.,caching  | nodes, layout     | transform | nodes)           | may | also be | rule. |     |     |     |     |     |
introducedtotheDAGduringthesketchgeneration. Rule1justsimplyskipsanodeifitisnotstrictlyinlinable.
Weproposeaderivation-basedenumerationapproachto Rule2alwaysinlinesstrictlyinlinablenodes.Sincethecondi-
generateallpossiblesketchesbyrecursivelyapplyingseveral tionsofrule1andrule2aremutuallyexclusive,astatewith
i>1canalwayssatisfyoneofthemandcontinuetoderive.
basicrules.ThisprocesstakesaDAGasaninputandreturns
alistofsketches.WedefinetheStates=(S,i),whereSis Rules3,4,and5dealwiththemulti-leveltilingandfusion
thecurrentpartiallygeneratedsketchfortheDAG,andiisthe fornodesthathavedatareuse.Rule3performsmulti-level
indexofthecurrentworkingnode.ThenodesinaDAGare tilingfordatareusablenodes.ForCPU,weusea“SSRSRS”
sortedinatopologicalorderfromoutputtoinput.Thederiva- tile structure, where “S” stands for one tile level of space
tionbeginsfromtheinitialnaiveprogramandthelastnode,or loops and “R” stands for one tile level of reduction loops.
theinitialstates=(naive program,indexof thelast node). Forexample,inthematmulC(i,j)=Â A[i,k] B[k,j],iand
|     |     |     |     |     |     |     |     |     | k   | ⇥   |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Then we try to apply all derivation rules to the states re- jarespaceloopsandkisareductionloop.The“SSRSRS”
cursively.Foreachrule,ifthecurrentstatesatisfiestheap- tile structure for matmul expands the original 3-level loop
plication condition,we apply the rule to s=(S,i) andget (i,j,k) into a 10-level loop (i ,j ,i ,j ,k ,i ,j ,k ,i ,j ).
|     |     |     |     |     |     |     |     |     | 0 0 1 | 1 0 2 2 | 1 3 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | ------- | ----- |
s 0 =(S,i)wherei 0 0 0 i.Thiswaytheindexi(workingnode) Althoughwedonotpermutethelooporder,thismulti-level

USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation    867

tilingcanalsocoversomecasesofreordering.Forexample, Winogradconvolution[30])andacceleratorintrinsics(e.g.,
the above 10-levelloopcan be specializedto justa simple TensorCore [37]) require specialtile structures to be effec-
reorder(k 0 ,j 2 ,i 3 )bysettingthelengthofotherloopstoone. tive.Althoughthetemplate-guidedsearchapproach(inTVM)
The"SSRSRS"tilestructureisgeneralforcompute-intensive cancraftanewtemplateforeverynewcase,itneedsagreat
denseoperators(e.g.,matmul,conv2d,conv3d)indeeplearn- amountofdesign effort. On the otherhand,the derivation-
ing, because they all consist of space loops and reduction basedsketchgenerationinAnsorisflexibleenoughtogen-
loops. erate the required structures for emerging algorithms and
Rule4performsmulti-leveltilingandalsofusesthefusible hardware,asweallowuserstoregisternewderivationrules
consumers. For example, we fuse the element-wise nodes andintegratethemseamlesslywithexistingrules.
(e.g.,ReLU,biasadd)intothetilednodes(e.g.,conv2d,mat-
mul).Rule5addsacachingnodeifthecurrentdata-reusable
4.2 RandomAnnotation
nodedoesnothaveafusibleconsumer.Forexample,thefi-
naloutputnodeinaDAGdoesnothaveanyconsumer,soit Thesketchesgeneratedbytheprevioussubsectionareincom-
directlywritesresultsintomainmemorybydefaultandthis
pleteprogramsbecausetheyonlyhavetilestructureswithout
isinefficientduetothehighlatencyofmemoryaccesses.By
specifictilesizesandloopannotations,suchasparallel,unroll,
addingacachenode,weintroduceanewfusibleconsumer andvectorization.Inthissubsection,weannotatesketchesto
intotheDAG,thenrule4canbeappliedtofusethisnewly
makethemcompleteprogramsforfine-tuningandevaluation.
addedcachenodeintothefinaloutputnode.Withthecache Givenalistofgeneratedsketches,werandomlypickone
nodefused,nowthefinaloutputnodewritesitsresultsintoa
|     |     |     |     | sketch, randomly | fill out tile | sizes, parallelize | some outer |
| --- | --- | --- | --- | ---------------- | ------------- | ------------------ | ---------- |
cacheblock,andthecacheblockwillbewrittentothemain
|     |     |     |     | loops, vectorize | some inner | loops, and unroll | a few inner |
| --- | --- | --- | --- | ---------------- | ---------- | ----------------- | ----------- |
memoryatoncewhenalldataintheblockiscomputed. loops. We also randomly change the computation location
Rule6canuserfactor[46]tofactorizeareductionloop
|     |     |     |     | of some nodes | in the program | to make a slight | tweak to |
| --- | --- | --- | --- | ------------- | -------------- | ---------------- | -------- |
intoaspacelooptobringmoreparallelism. the tile structure. All“random” in this subsection means a
Examples. Figure 5 shows three examples of the gener- uniform distribution over all valid values. If some special
| ated sketches. | The sketches | are different | from the manual |     |     |     |     |
| -------------- | ------------ | ------------- | --------------- | --- | --- | --- | --- |
algorithmsrequirecustomannotationstobeeffective(e.g.,
templates in TVM, because the manual templates specify specialunrolling),weallowuserstogivesimplehintsinthe
bothhigh-levelstructuresandlow-leveldetailswhilesketches
computationdefinitiontoadjusttheannotationpolicy.Finally,
onlydefinehigh-levelstructures.Fortheexampleinput1,the sincechangingthelayoutofconstanttensorscanbedonein
sortedorderofthefournodesintheDAGis(A,B,C,D).To compilationtimeandbringsnoruntimeoverhead,werewrite
derivethesketchesfortheDAG,westartfromoutputnode
thelayoutsoftheconstanttensorsaccordingtothemulti-level
D(i=4)andapplyrulestothenodesonebyone.Specifically, tilestructuretomakethemascache-friendlyaspossible.This
thederivationforgeneratedsketch1is:
optimizationiseffectivebecausetheweighttensorsofconvo-
Rule1 Rule4 lutionordenselayersareconstantsforinferenceapplications.
| Input 1 | s(S ,i=4) | s(S ,i=3) |     |     |     |     |     |
| ------- | --------- | --------- | --- | --- | --- | --- | --- |
! 0 ! 1 ! ExamplesofrandomsamplingareshowninFigure5.The
|     |     | Rule1 | Rule1 |     |     |     |     |
| --- | --- | ----- | ----- | --- | --- | --- | --- |
s(S 2 ,i=2) s(S 3 ,i=1) Sketch1 sampled program might have fewer loops than the sketch
|     |     | ! | ! |     |     |     |     |
| --- | --- | ---- | ---- | --- | --- | --- | --- |
becausetheloopswithlengthonearesimplified.
Fortheexampleinput2,thesortedorderofthefivenodes
| is (A,B,C,D,E). | Similarly, | we start | from the output node |     |     |     |     |
| --------------- | ---------- | -------- | -------------------- | --- | --- | --- | --- |
E(i=5)andapplyrulesrecursively.Thegeneratedsketch2 4.3 GPUSupport
isderivedby:
|         |           |           |       | For GPU, | we change the multi-level | tiling | structure from |
| ------- | --------- | --------- | ----- | -------- | ------------------------- | ------ | -------------- |
|         |           | Rule5     | Rule4 |          |                           |        |                |
| Input 2 | s(S ,i=5) | s(S ,i=5) |       |          |                           |        |                |
! 0 ! 1 ! "SSRSRS"to"SSSRRSRS"tomatchthearchitectureofGPU.
Rule1 Rule1 TheloopsinthefirstthreespacetilesareboundtoBlockIdx,
|     | s(S 2 ,i=4) | s(S 3 ,i=3) |     |     |     |     |     |
| --- | ----------- | ----------- | --- | --- | --- | --- | --- |
! ! virtualthread(forreducingbankconflicts),andThreadIdx,
|     |     | Rule2 | Rule1 |     |     |     |     |
| --- | --- | ----- | ----- | --- | --- | --- | --- |
s(S 4 ,i=2) s(S 5 ,i=1) Sketch2 respectively.Weaddtwosketchderivationrules,oneforuti-
|     |     | ! | ! |     |     |     |     |
| --- | --- | ---- | ---- | --- | --- | --- | --- |
lizingsharedmemorybyinsertingacachingnode(similarto
Similarly,thegeneratedsketch3isderivedby:
Rule5)andtheotherforcross-threadreduction(similarto
|       |               | Rule6         | Rule1   | Rule6).                                           |     |     |     |
| ----- | ------------- | ------------- | ------- | ------------------------------------------------- | --- | --- | --- |
| Input | 2 s(S 0 ,i=5) | s(S           | 1 ,i=4) |                                                   |     |     |     |
|       | !             | !          | !    |                                                   |     |     |     |
|       |               | Rule1         | Rule2   |                                                   |     |     |     |
|       | s(S 2 ,i=3)   | s(S           | 3 ,i=2) |                                                   |     |     |     |
|       |               | !          | !    | 5 PerformanceFine-tuning                          |     |     |     |
|       | s(S ,i=1)     | Rule1 Sketch3 |         |                                                   |     |     |     |
|       | 4             |               |         | Theprogramssampledbytheprogramsamplerhavegoodcov- |     |     |     |
!
Customization. While the presented rules are practical erageofthesearchspace,buttheirqualitiesarenotguaranteed.
enoughtocoverthestructuresformostoperators,thereareal- Thisisbecausetheoptimizationchoices,suchastilestruc-
waysexceptions.Forexample,somespecialalgorithms(e.g., tureandloopannotations,areallrandomlysampled.Inthis
868    14th USENIX Symposium on Operating Systems Design and Implementation USENIX Association

| Example Input 1: |     |     | Generated sketch 1 |     |     |     |     |     | Sampled program 1   |     |     |     |
| ---------------- | --- | --- | ------------------ | --- | --- | --- | --- | --- | ------------------- | --- | --- | --- |
* The mathmetical expression: for i.0 in range(TILE_I0): parallel i.0@j.0@i.1@j.1 in range(256):
|     |    |     | for j.0 in |     | range(TILE_J0): |     |     |     |            |            |     |     |
| --- | --- | --- | ---------- | --- | --------------- | --- | --- | --- | ---------- | ---------- | --- | --- |
|     |     |     |            |     |                 |     |     |     | for k.0 in | range(32): |     |     |
!",$ =&'[",)]	×	/[),$] for i.1 in range(TILE_I1): for i.2 in range(16):
|     | ,   |     |     | for j.1 in | range(TILE_J1): |     |     |     |     | unroll k.1 in | range(16): |     |
| --- | --- | --- | --- | ---------- | --------------- | --- | --- | --- | --- | ------------- | ---------- | --- |
0",$ =max	(!",$,0.0)
|     |     |     |     | for k.0 in |     | range(TILE_K0): |     |     |     | unroll | i.3 in range(4): |     |
| --- | --- | --- | --- | ---------- | --- | --------------- | --- | --- | --- | ------ | ---------------- | --- |
where 0≤",$,)<512 for i.2 in range(TILE_I2): vectorizej.3 in range(16):
|     |     |     |     |     | for j.2 in | range(TILE_J2): |     |     |     | C[...] += | A[...] * B[...] |     |
| --- | --- | --- | --- | --- | ---------- | --------------- | --- | --- | --- | --------- | --------------- | --- |
* The corresponding naive program: for k.1 in range(TILE_I1): for i.4 in range(64):
for i in range(512):
|     |     |     |     |     | for | i.3 in range(TILE_I3): |     |     | vectorize |     | j.4 in range(16): |     |
| --- | --- | --- | --- | --- | --- | ---------------------- | --- | --- | --------- | --- | ----------------- | --- |
for j in range(512): for j.3 in range(TILE_J3): D[...] = max(C[...], 0.0)
|     | for k in   | range(512):       |     |     |        |                           |                 |     |     |     |     |     |
| --- | ---------- | ----------------- | --- | --- | ------ | ------------------------- | --------------- | --- | --- | --- | --- | --- |
|     |            |                   |     |     |        | C[...] +=                 | A[...] * B[...] |     |     |     |     |     |
|     | C[i, j] += | A[i, k] * B[k, j] |     | for | i.4 in | range(TILE_I2 * TILE_I3): |                 |     |     |     |     |     |
for i in range(512): for j.4 in range(TILE_J2 * TILE_J3): Sampled program 2
for j in range(512): D[...] = max(C[...], 0.0) parallel i.2 in range(16):
|     | D[i, j] = | max(C[i, j], 0.0) |     |     |     |     |     |     | for        | j.2 in range(128): |             |     |
| --- | --------- | ----------------- | --- | --- | --- | --- | --- | --- | ---------- | ------------------ | ----------- | --- |
|     |           |                   |     |     |     |     |     |     | for k.1 in |                    | range(512): |     |
* The corresponding DAG:
for i.3 in range(32):
|     |     |     |                    |                |     |     |     |     |          | vec t o r | i z e j. 3   i n  | r a n g e ( 4 ) :  |
| --- | --- | --- | ------------------ | -------------- | --- | --- | --- | --- | -------- | --------- | ----------------- | ------------------ |
|     |     | A   | Generated sketch 2 |                |     |     |     |     |          |           |                   |                    |
|     |     | C D |                    |                |     |     |     |     |          | C [ . .   | . ]  += A [ . . . | ]  *   B [ . . . ] |
|     |     | B   | for                | i in range(8): |     |     |     |     | parallel | i.4 in    | range(512):       |                    |
for k in range(512):
|                   |     |             |            |                        |                 |         |            |     | for j.4 in | range(512):      |     |     |
| ----------------- | --- | ----------- | ---------- | ---------------------- | --------------- | ------- | ---------- | --- | ---------- | ---------------- | --- | --- |
|                   |     |             |            | C[i, j] =              | max(A[i,k],     | 0.0) if | k<400 else | 0   | D[...] =   | max(C[...], 0.0) |     |     |
| Example Input 2:  |     |             | for        | i.0 in range(TILE_I0): |                 |         |            |     |            |                  |     |     |
|                   |     |             | for j.0 in |                        | range(TILE_J0): |         |            |     |            |                  |     |     |
| * The mathmetical |     | expression: |            |                        |                 |         |            |     |            |                  |     |     |
for i.1 in range(TILE_I1):
/",= =max	('",=,0.0) for j.1 in range(TILE_J1): Sampled program 3
|     | 	/ [ " ,) ] , | ) < 4 0 0 |     |     |     |     |     |     |     |     |     |     |
| --- | ------------- | --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
![",)]=> for   k.0   i n r an g e ( TI L E _ K 0 ) : par a l l e l i. 0   i n  r a n g e ( 8):
|      | 		  		 		 	0 		 	, | ) ≥ 4 0 0 |     | f   | or i .2   in |   r a ng e ( T I L E   | _ I 2): |     |           |               |                  |     |
| ---- | ------------------- | --------- | --- | --- | ------------ | ---------------------- | ------- | --- | --------- | ------------- | ---------------- | --- |
|      |                     |           |     |     | for j.2 in   | range(TILE_J2):        |         |     | f o r     |  k   in r a n | g e ( 5 1 2 ) :  |     |
| A",$ | =&![",)]	×	0[),$]   |           |     |     |              |                        |         |     | C[i, j] = |               | max(A[i,k],0.0)  |     |
|      |                     |           |     |     | for k.1 in   | range(TILE_I1):        |         |     |           |               |                  |     |
|      | ,                   |           |     |     | for          | i.3 in range(TILE_I3): |         |     |           |               | if k < 400 else  | 0   |
where 0≤"<8, 0≤$<4,		 for j.3 in range(TILE_J3): for k.0 in range(512):
|                                    |                  |     |     |            |                                  |                           |                 |     | vectorize       |                 | j.3 in range(4): |     |
| ---------------------------------- | ---------------- | --- | --- | ---------- | -------------------------------- | ------------------------- | --------------- | --- | --------------- | --------------- | ---------------- | --- |
|                                    | 0≤)<512,	0≤=<400 |     |     |            |                                  | E.cache[...] +=           | C[...] * D[...] |     |                 |                 |                  |     |
|                                    |                  |     |     | for        | i.4 in range(TILE_I2 * TILE_I3): |                           |                 |     |                 | E.cache[...] += | C[...] * D[...]  |     |
| * The corresponding naive program: |                  |     |     |            |                                  |                           |                 |     | vectorizej.4 in |                 | range(4):        |     |
|                                    |                  |     |     | for j.4 in |                                  | range(TILE_J2 * TILE_J3): |                 |     |                 |                 |                  |     |
for i in range(8): E[...] = E.cache[...] E[...] = E.cache[...]
for l in range(400):
|     | B[i, l] = | max(A[i, l], 0.0) | Generated sketch 3 |     |     |     |     |     |     |     |     |     |
| --- | --------- | ----------------- | ------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
for i in range(8):
|     | for k in range(512): |     | for | i in range(8): |     |     |     |     | Sampled  program 4   |     |     |     |
| --- | -------------------- | --- | --- | -------------- | --- | --- | --- | --- | -------------------- | --- | --- | --- |
C[i, k] = B[i, k] if k < 400 else 0 for k in range(512): parallel i in range(8):
for i in range(8): C[i, k] = max(A[i, k], 0.0) if k < 400 else 0 for k in range(512):
|                          | for j in range(4): |                   | for | i in range(8): |                        |                 |     |     |          | C[i, k] =      | ...             |     |
| ------------------------ | ------------------ | ----------------- | --- | -------------- | ---------------------- | --------------- | --- | --- | -------- | -------------- | --------------- | --- |
|                          | for k in           | range(512):       | for | j in range(4): |                        |                 |     |     | for      | j in range(4): |                 |     |
|                          |                    |                   |     | for k_o        | in range(TILE_K0):     |                 |     |     |          |                |                 |     |
|                          | E[i, j] +=         | C[i, k] * D[k, j] |     |                |                        |                 |     |     | unroll   | k_o            | in range(32):   |     |
|                          |                    |                   |     | for            | k_i in range(TILE_KI): |                 |     |     |          | vectorizedk_i  | in range(16):   |     |
|                          |                    |                   |     | E.rf[...] +=   |                        | C[...] * D[...] |     |     |          |                |                 |     |
| * The corresponding DAG: |                    |                   |     |                |                        |                 |     |     |          | E.rf[...] +=   | C[...] * D[...] |     |
|                          |                    |                   | for | i in range(8): |                        |                 |     |     | parallel | i in range(8): |                 |     |
|                          | A                  | B C               | for | j in range(4): |                        |                 |     |     | for      | j in range(4): |                 |     |
|                          |                    | E                 |     | for k_i        | in range(TILE_KI):     |                 |     |     | unroll   | k_i            | in range(16):   |     |
|                          |                    | D                 |     | E[...] +=      | E.rf[...]              |                 |     |     |          | E[...] +=      | E.rf[...]       |     |
Figure5:Examplesofgeneratedsketchesandsampledprograms.Thisfigureshowstwoexampleinputs,threegeneratedsketches
andfoursampledprograms.Thecodeexampleispseudocodeinapython-likesyntax.
section,weintroducetheperformancetunerthatfine-tunes fasterthantheactualmeasurement.Itallowsustocompare
theperformanceofthesampledprogramsviaevolutionary tensofthousandsofprogramsinthesearchspaceinseconds,
searchandalearnedcostmodel. andpickthepromisingonestodoactualmeasurements.
Thefine-tuningisperformediteratively.Ateachiteration,
wefirstuseevolutionarysearchtofindasmallbatchofpromis-
|     |     |     |     |     |     | 5.1 | EvolutionarySearch |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | --- | --- | --- | --- |
ingprogramsaccordingtoalearnedcostmodel.Wethenmea-
suretheseprogramsonhardwaretogettheactualexecution
Evolutionarysearch[54]isagenericmeta-heuristicalgorithm
timecost.Finally,theprofilingdatagotfrommeasurementis
inspiredbybiologicalevolution.Byiterativelymutatinghigh-
usedtore-trainthecostmodeltomakeitmoreaccurate.
qualityprograms,wecangeneratenewprogramswithpoten-
Theevolutionarysearchusesrandomlysampledprograms tiallyhigherquality.Theevolutionstartsfromthesampled
as well as high-quality programs from the previous mea- initialgeneration.Togeneratethenextgeneration,wefirstse-
surementastheinitialpopulationandappliesmutationand lectsomeprogramsfromthecurrentgenerationaccordingto
crossovertogeneratethenextgeneration.Thelearnedcost certainprobabilities.Theprobabilityofselectingaprogramis
modelisusedtopredictthefitnessofeachprogram,whichis proportionaltoitsfitnesspredictedbythelearnedcostmodel
thethroughputofoneprograminourcase.Werunevolution (§5.2),meaningthattheprogramwithahigherperformance
forafixednumberofgenerationsandpickthebestprograms scorehasahigherprobabilitytobeselected.Fortheselected
foundduringthesearch.Weleveragealearnedcostmodelbe- programs,werandomlyapplyoneoftheevolutionoperations
causethecostmodelcangiverelativelyaccurateestimations togenerateanewprogram.Basically,fordecisionswemade
ofthefitnessofprogramswhilebeingordersofmagnitudes duringsampling(§4.2),wedesigncorrespondingevolution
USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation    869

operationstorewriteandfine-tunethem. lectedmeasurementdataisthenusedtoupdatethecostmodel.
Tilesizemutation.Thisoperationscanstheprogramand Inthisway,theaccuracyofthelearnedcostmodelisgrad-
randomlyselectsatiledloop.Forthistiledloop,itdividesa uallyimprovedtomatchthetargethardware.Consequently,
tilesizeofonetilelevelbyarandomfactorandmultipliesthis the evolutionary search gradually generates higher-quality
factortoanotherlevel.Sincethisoperationkeepstheproduct programsforthetargethardwareplatform.
of tile sizes equal to the original loop length,the mutated
UnlikethesearchalgorithmsinTVMandFlexTensorthat
programisalwaysvalid.
canonlyworkinafixedgrid-likeparameterspace,theevolu-
Parallelmutation.Thisoperationscanstheprogramand tionaryoperationsinAnsorarespecificallydesignedforten-
randomlyselectsaloopthathasbeenannotatedwithparallel. sorprograms.Theycanbeappliedtogeneraltensorprograms
Forthisloop,thisoperationchangestheparallelgranularity andcanhandleasearchspacewithcomplicateddependency.
by eitherfusing its adjacent loop levels or splitting it by a UnliketheunfoldingrulesinHalideauto-scheduler,theseop-
factor. erationscanperformout-of-ordermodificationstoprograms,
Pragmamutation.Someoptimizationsinaprogramare addressingthesequentiallimitations.
specifiedbycompiler-specificpragma.Thisoperationscans
theprogramandrandomlyselectsapragma.Forthispragma,
thisoperationrandomlymutatesitintoanothervalidvalue.
For example,our underlying code generator supports auto
5.2 LearnedCostModel
unrollingwithamaximumnumberofstepsbyprovidingan
auto_unroll_max_step=Npragma.Werandomlytweakthe
Acostmodelisnecessaryforestimatingtheperformanceof
numberN.
programsquicklyduringthesearch.Weadoptalearnedcost
Computationlocationmutation.Thisoperationscansthe
modelsimilartorelatedworks[2,12]withnewlydesigned
programandrandomlyselectsaflexiblenodethatisnotmulti-
program features. A system based on learned cost models
leveltiled(e.g.,apaddingnodeintheconvolutionlayer).For
has greatportability because a single modeldesign can be
thisnode,theoperationrandomlychangesitscomputation
reusedfordifferenthardwarebackendsbyfeedingindifferent
locationtoanothervalidattachpoint.
trainingdata.
Node-basedcrossover.Crossoverisanoperationtogener-
Sinceourtargetprogramsaremainlydataparalleltensor
atenewoffspringbycombiningthegenesfromtwoormore
programs,whicharemadebymultipleinterleavedloopnests
parents. The genes ofa program in Ansorare its rewriting
with several assignment statements as the innermost state-
steps.EveryprogramgeneratedbyAnsorisrewrittenfrom
ments,wetrainthecostmodeltopredictthescoreofonein-
itsinitialnaiveimplementation.Ansorpreservesacomplete
nermostnon-loopstatementinaloopnest.Forafullprogram,
rewritinghistoryforeachprogramduringsketchgeneration
wemakepredictionsforeachinnermostnon-loopstatement
andrandomannotation.Wecantreatrewritingstepsasthe
andaddthepredictionsupasthescore.Webuildthefeature
genesofaprogrambecausetheydescribehowthisprogram
vectorforaninnermostnon-loopstatementbyextractingfea-
isformedfromtheinitialnaiveone.Basedonthis,wecan
turesinthecontextofafullprogram.Theextractedfeatures
generate a new program by combining the rewriting steps
includearithmeticfeaturesandmemoryaccessfeatures. A
of two existing programs. However, arbitrarily combining
detailed list of extracted features is in an appendix of the
rewriting steps from two programs might breakthe depen-
extendedversionofthispaper[58].
denciesinstepsandcreateaninvalidprogram.Asaresult,
thegranularityofcrossoveroperationinAnsorisbasedon We use weighted squared erroras the loss function. Be-
nodesintheDAG,becausetherewritingstepsacrossdifferent causewemostlycareaboutidentifyingthewell-performing
nodesusuallyhavelessdependency.Ansorrandomlyselects programs from the search space, we put more weight on
oneparentforeachnodeandmergestherewritingstepsof the programs that run faster. Specifically, the loss func-
selectednodes.Whentherearedependenciesbetweennodes, tion of the model f on a program P with throughput y is
A tic n s s . o A r n tr s i o es rf to ur a th n e a r ly v z e e ri a fi n e d s a th dj e u m st e t r h g e e s d te p p r s og w ra it m h s si t m o p g l u e a h ra e n u t r e is e - w lo h s e s( re f, S P ( , P y) ) = is w th p e (Â se s t2 S o ( f P) in f n (s e ) rm  o y s ) t 2 n = on y - ( lo Â o s p2 S s ( t P a ) te f m (s) en  ts y) in 2
thefunctionalcorrectness.Theverificationissimplebecause P. We directly use the throughput y as weight. We train a
Ansor only uses a small set of loop transformation rewrit- gradientboostingdecisiontree[9]astheunderlyingmodel
ingsteps,andtheunderlyingcodegeneratorcancheckthe f.Asinglemodelistrainedforalltensorprogramscoming
correctnessbydependencyanalysis. fromallDAGs,andwenormalizethethroughputofallpro-
Theevolutionarysearchleveragesmutationandcrossover gramscomingfromthesameDAGtobeintherangeof[0,1].
to generate a new set of candidates repeatedly for several WhenoptimizingaDNN,thenumberofmeasuredprograms
roundsandoutputsasmallsetofprogramswiththehighest aretypicallylessthan30,000.Trainingagradientboosting
scores.Theseprogramswillbecompiledandmeasuredonthe decisiontreeisveryfastonsuchasmalldatasets,sowetrain
targethardwaretoobtaintherealrunningtimecost.Thecol- anewmodeleverytimeinsteadofdoingincrementalupdates.
870 14th USENIX Symposium on Operating Systems Design and Implementation USENIX Association

| 6 TaskScheduler |     |     |     |     |     |     |     | f =Âm |         | w      | g (t) |     |     |     |
| --------------- | --- | --- | --- | --- | --- | --- | --- | ----- | ------- | ------ | ----- | --- | --- | --- |
|                 |     |     |     |     |     |     |     | 1     | j=1 Â i | S(j) i | i     |     |     |     |
|                 |     |     |     |     |     |     |     |       | 2       |        | ⇥     |     |     |     |
=Âm
|                                                  |     |     |     |     |     |     |     | f 2 | max(Â | S(j) | w i | g i (t),L j | )   |     |
| ------------------------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | ----- | ---- | --- | ----------- | --- | --- |
| ADNNcanbepartitionedintomanyindependentsubgraphs |     |     |     |     |     |     |     |     | j=1   | i    | ⇥   |             |     |     |
|                                                  |     |     |     |     |     |     |     |     |       | 2 B  |     | 1           |     |     |
( e. g . , co nv 2d + r e lu ) . F o r s o m e s u bg r a p h s, s p en d in gt im e in f = (’m j )m
|     |     |     |     |     |     |     |     | 3  | j=1Âi | w   | gi(t) |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | ----- | --- | --- | --- |
S(j) i⇥
tu n i n g th em d o e s n o t i m p r o ve t h e e n d - to -e n d D N N p er fo r- =Âm 2
|     |     |     |     |     |     |     |     | f   | Â   | w i | max(g | i (t),ES(g | i ,t)) |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | ---------- | ------ | --- |
mancesignificantly.Thisisduetotworeasons:either(1)the 4 j=1 i S(j) ⇥
2
subgraphisnotaperformancebottleneck,or(2)tuningbrings
Table2:Examplesofobjectivefunctionsformultipleneural
onlyminimalimprovementinthesubgraph’sperformance.
networks
Toavoidwastingtimeontuningunimportantsubgraphs,
Ansor dynamically allocates different amounts of time re- Tominimizetheend-to-endlatencyofasingleDNN,we
s o u r c es t o d if fe r e n t s u b g ra p h s . T a k e R e sN e t - 5 0 f o r e x a m p le , i t Ân
|     |     |     |     |     |     | can | define | f(g | 1 ,g 2 ,...,g | n ) = | w   | i g i , where | w i | is the |
| --- | --- | --- | --- | --- | --- | --- | ------ | --- | ------------- | ----- | --- | ------------- | --- | ------ |
|     |     |     |     |     |     |     |        |     |               |       | i=1 | ⇥             |     |        |
h a s 2 9 u n iq u e s u b g r a p h s a ft e r t h e g r ap h p a r t it io n i n g . M o s t o f number of appearances of task i in the DNN. This formu-
thesesubgraphsareconvolutionlayerswithdifferentshapes
|     |     |     |     |     |     | lationisstraightforwardbecause |     |     |     |     | f isanapproximationofthe |     |     |     |
| --- | --- | --- | --- | --- | --- | ------------------------------ | --- | --- | --- | --- | ------------------------ | --- | --- | --- |
configurations(inputsize,kernelsize,stride,etc).Weneed
end-to-endDNNlatency.
togeneratedifferentprogramsfordifferentconvolutionlay- WhentuningasetofDNNs,thereareseveraloptions.Ta-
ersbecausethebesttensorprogramdependsontheseshape
|     |     |     |     |     |     | ble | 2 shows | a   | number | of example |     | objective | functions | for |
| --- | --- | --- | --- | --- | --- | --- | ------- | --- | ------ | ---------- | --- | --------- | --------- | --- |
configurations.Inreality,usersmayhavemultipleDNNsfor
tuningmultipleDNNs.LetmbethenumberofDNNs,S(j)is
alltheirapplications.Thisleadstomoresubgraphsaswellas
|     |     |     |     |     |     | thesetoftasksthatbelongtoDNN |     |     |     |     | j.  | f 1 addsupthelatency |     |     |
| --- | --- | --- | --- | --- | --- | ---------------------------- | --- | --- | --- | --- | --- | -------------------- | --- | --- |
moreopportunitiestoreducethetotaltuningtime,because
ofeveryDNN,whichmeanstooptimizethecostofapipeline
we can share and reuse knowledge between subgraphs. A thatsequentiallyrunsallDNNsonce.In f ,wedefineL as
|     |     |     |     |     |     |     |     |     |     |     |     | 2   |     | j   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
subgraphcanalsoappearmultipletimesinaDNNoracross
|     |     |     |     |     |     | thelatencyrequirementofDNN |     |     |     |     | j,meaningthatwedonot |     |     |     |
| --- | --- | --- | --- | --- | --- | -------------------------- | --- | --- | --- | --- | -------------------- | --- | --- | --- |
differentDNNs.
wanttospendtimeonaDNNifitslatencyhasalreadymet
Wedefineataskasaprocessperformedtogeneratehigh-
|     |     |     |     |     |     | therequirement.In |     |     | f 3 | ,wedefineB | j   | asthereferencelatency |     |     |
| --- | --- | --- | --- | --- | --- | ----------------- | --- | --- | --- | ---------- | --- | --------------------- | --- | --- |
performanceprogramsforasubgraph.Itmeansthatoptimiz-
|     |     |     |     |     |     | of  | a DNN | j. As | a result,our |     | goal is | to maximize | the | geo- |
| --- | --- | --- | --- | --- | --- | --- | ----- | ----- | ------------ | --- | ------- | ----------- | --- | ---- |
ingasingleDNNrequiresfinishingdozensoftasks(e.g.,29 metricmeanofspeedupagainstthegivenreferencelatency.
tasksforResNet-50).Ansor’staskschedulerallocatestime
|     |     |     |     |     |     | Finallyin |     | f 4 ,we | define | a function | ES(g,t) | i   | thatreturns | an  |
| --- | --- | --- | --- | --- | --- | --------- | --- | ------- | ------ | ---------- | ------- | --- | ----------- | --- |
resourcestotasksinaniterativemanner. Ateachiteration, earlystoppingvaluebylookingatthehistoryoflatencyof
Ansorselectsatask,generatesabatchofpromisingprograms taski.Itcanachievetheeffectofper-taskearlystopping.
forthesubgraph,andmeasurestheprogramonhardware.We
definesuchaniterationasoneunitoftimeresources.When
6.2 OptimizingwithGradientDescent
weallocateoneunitoftimeresourcestoatask,thetaskob-
tainsanopportunitytogenerateandmeasurenewprograms, Weproposeaschedulingalgorithmbasedongradientdescent
whichalsomeansthechancetofindbetterprograms.Wenext
toefficientlyoptimizetheobjectivefunction.Giventhecur-
presenttheformulationoftheschedulingproblemandour
rentallocationt,theideaistoapproximatethegradientofthe
| solution. |     |     |     |     |     |                   |     |     | ∂f  |                                 |     |     |     |     |
| --------- | --- | --- | --- | --- | --- | ----------------- | --- | --- | --- | ------------------------------- | --- | --- | --- | --- |
|           |     |     |     |     |     | objectivefunction |     |     |     | inordertochoosethetaskisuchthat |     |     |     |     |
∂ti
∂f
|     |     |     |     |     |     | i=argmax |     |     | .Weapproximatethegradientbymakingan |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | -------- | --- | --- | ----------------------------------- | --- | --- | --- | --- | --- |
i|∂ti|
6.1 ProblemFormulation optimisticguessandconsideringthesimilaritybetweentasks.
Thederivationisinanappendixoftheextendedversionof
WhentuningaDNNorasetofDNNs,ausercanhavevarious thispaper[58].Weapproximatethegradientby
typesofgoals,forexample,reducingaDNN’slatency,meet-
|                                                  |      |        |     |                 |             |     | ∂f  | ∂f   | g(t) | g(t | Dt) |     |     |     |
| ------------------------------------------------ | ---- | ------ | --- | --------------- | ----------- | --- | --- | ---- | ---- | --- | --- | --- | --- | --- |
| inglatencyrequirementsforasetofDNNs,orminimizing |      |        |     |                 |             |     |     |      | i i  | i   | i   |     |     |     |
|                                                  |      |        |     |                 |             |     |     | (a   |      |    |  + |     |     |     |
|                                                  |      |        |     |                 |             |     | ∂t  | ⇡ ∂g |      | Dt  |     |     |     |     |
| tuning time                                      | when | tuning | no  | longer improves | DNN perfor- |     | i   | i    |      |     |     |     |     |     |
mancesignificantly.Wethusprovideusersasetofobjective g (t ) C
|     |     |     |     |     |     |     | (1  | a)(min( |     | i i | ,b  | i   | g(t)))) |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------- | --- | --- | --- | --- | ------- | --- |
i i
functionstoexpresstheirgoals.Userscanalsoprovidetheir   t i max k N(i) V k
2
ownobjectivefunctions.
whereDt isasmallbackwardwindowsize,g(t)andg(t
|                                   |     |     |                               |     | Zn         |     |           |     |          |         |     |              | i i  | i i    |
| --------------------------------- | --- | --- | ----------------------------- | --- | ---------- | --- | --------- | --- | -------- | ------- | --- | ------------ | ---- | ------ |
| Supposetherearentasksintotal.Lett |     |     |                               |     | betheallo- |     |           |     |          |         |     |              |      |       |
|                                   |     |     |                               |     | 2          | Dt) | are known |     | from the | history | of  | allocations. | N(i) | is the |
| cationvector,wheret               |     |     | isthenumberoftimeunitsspenton |     |            |     |           |     |          |         |     |              |      |        |
i set of similar tasks of i,C is the number of floating point
| taski.Lettheminimumsubgraphlatencytaskiachievesbe   |     |     |     |     |     |           |     |         |       | i      |            |     |          |       |
| --------------------------------------------------- | --- | --- | --- | --- | --- | --------- | --- | ------- | ----- | ------ | ---------- | --- | -------- | ----- |
|                                                     |     |     |     |     |     | operation |     | in task | i and | V k is | the number | of  | floating | point |
| afunctionoftheallocationvectorg(t).Lettheend-to-end |     |     |     | i   |     |           |     |         |       |        |            |     |          |       |
operationpersecondwecanachieveintaskk.Theparameter
| cost of | the DNNs | be  | a function | of the | latency of the sub- |     |     |     |     |     |     |     |     |     |
| ------- | -------- | --- | ---------- | ------ | ------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
aandbcontroltheweighttotrustsomepredictions.
| graphs f(g | 1 (t),g | 2 (t),...,g | 3 (t)).Ourobjectiveistominimize |     |     |     |     |     |     |     |     |     |     |     |
| ---------- | ------- | ----------- | ------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Torunthealgorithm,Ansorstartsfromt=0andwarms
theend-to-endcost:
|     |     |     |     |     |     | up  | with a | round | of round-robin |     | to get | an initial | allocation |     |
| --- | --- | --- | --- | --- | --- | --- | ------ | ----- | -------------- | --- | ------ | ---------- | ---------- | --- |
minimize f(g 1 (t),g 2 (t),...,g 3 (t)) vectort=(1,1,...,1).Afterthewarm-up,ateachiteration,we
USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation    871

computethegradientofeachtaskandpickargmax ∂f .Then andFlexTensoraretemplate-guidedsearchframeworksbased
i|∂ti|
weallocatetheresourceunittotaskiandupdatetheallocation onTVM.SinceHalideauto-schedulerdoesnothaveapre-
vectort =t +1. The optimization process continues until trainedcostmodelforAVX-512,wedisabledAVX-512for
i i
werunoutofthetimebudget.Toencourageexploration,we theevaluationin§7.1and§7.2.Foreveryoperator,weuse
adoptae-greedystrategy[47],whichpreservesaprobability thebestlayoutavailableineachframework,buttheinputand
ofetorandomlyselectatask. outputtensorsmustnotbepacked.
TakingthecaseofoptimizingforasingleDNN’send-to- Search settings. We let search frameworks (i.e.,Halide
endlatencyforexample,Ansorprioritizesasubgraphthathas auto-scheduler, FlexTensor, AutoTVM, and Ansor) to run
ahighinitiallatencybecauseouroptimisticguesssayswe search orauto-tuning with up to 1,000 measurementtrials
canreduceitslatencyquickly.Later,ifAnsorspendsmany per test case. This means each framework can measure at
iterations on it without observing a decrease in its latency, most80 1,000programsforauto-tuninginthisevaluation.
Ansorleavesthesubgraphbecauseits ∂f decreases. Usingth ⇥ esamenumberofmeasurementtrialsmakesitafair
|∂ti|
comparisonwithoutinvolvingimplementationdetails.Inaddi-
tion,using1,000measurementtrialspertestcaseistypically
7 Evaluation
enoughforthesearchtoconvergeintheseframeworks.
The core ofAnsoris implementedin C++ withabout12K Normalization. Figure 6 shows the normalized perfor-
mance.Foreachtestcase,wenormalizethethroughputsto
linesofcode(3Kforthesearchpolicyand9Kforotherinfras-
thebestperformingframework.Wethenplotthegeometric
tructure).Ansorgeneratesprogramsinitsownintermediate
meanofthefourshapesofeachoperator.Thegeometricmean
representation(IR).TheseprogramsarethenloweredtoTVM
isalsonormalizedtothebestperformingframework,sothe
IRforcodegenerationtargetingvarioushardwareplatforms.
best framework has a normalized performance of 1 in the
AnsoronlyutilizesTVMasadeterministiccodegenerator.
figure. The error bar denotes the standard deviation of the
We evaluate the performance of generated programs on
normalizedthroughputoffourshapesofeachoperator.
threelevels:singleoperator,subgraph,andentireneuralnet-
work.Foreachlevelofevaluation,wecompareAnsoragainst Results. As shown in the Figure 6,Ansor performs the
thestate-of-the-artsearchframeworksandhardware-specific best or equally the best in all operator and batch size set-
manuallibraries.Wealsoevaluatethesearchefficiencyand tings. Ansor outperforms existing search frameworks by
theeffectivenessofeachcomponentinAnsor. 1.1 22.5 .TheperformanceimprovementsofAnsorcome
 ⇥
The generated tensor programs are benchmarked on frombothitslargesearchspaceandeffectiveexplorationstrat-
three hardware platforms: an IntelCPU (18-core Platinum egy.Formostoperators,wefoundthebestprogramgenerated
8124M@3.0GHz),anNVIDIAGPU(V100),andanARM byAnsorisoutsidethesearchspaceofexistingsearchframe-
CPU(4-coreCortex-A53@1.4GHzontheRaspberryPi3b+). works because Ansoris able to explore more optimization
Weusefloat32asthedatatypeforallevaluations. combinations.Forexample,thesignificantspeeduponNRM
isbecauseAnsorcanparallelizereductionloops,whileother
frameworks do not. The large speedup on T2D is because
7.1 SingleOperatorBenchmark
Ansorcanusecorrecttilestructuresandunrollingstrategiesto
Workloads. We first evaluate Ansor on a set of common letthecodegeneratorsimplifythemultiplicationofzerosin
deeplearningoperators,including1D,2D,and3Dconvolu- stridedtransposedconvolution.Incontrast,otherframeworks
tion(C1D,C2D,andC3Drespectively),matrixmultiplica- failto capturemanyeffective optimizations in theirsearch
tion(GMM),groupconvolution(GRP),dilatedconvolution space,makingthemunabletofindtheprogramsthatAnsor
(DIL)[57],depth-wiseconvolution(DEP)[24],transposed2D does.Forexample,theunfoldingrulesinHalidedonotsplit
convolution(T2D)[40],capsule2Dconvolution(CAP)[23], thereductionloopinGMManddonotsplitreductionloops
and matrix 2-norm (NRM). Foreach operator,we select 4 inC2Dwhenpaddingiscomputedoutsideofreductionloops.
common shape configurations and evaluate them withtwo The templates in AutoTVM have limitedtile structures,as
batch sizes (1 and 16). In total,there are 10 operators 4 theycannotcoverthestructureof“GeneratedSketch1”in
⇥
shapeconfigurations 2batchsize=80testcases.Theshape Figure 5. The template in FlexTensor does not change the
⇥
configurationsusedcanbefoundinanappendixoftheex- computationlocationofpadding.ThetemplateinFlexTensor
tendedversionofthispaper[58].Werunthesetestcaseson failstorunforreductionoperatorslikeNRM.
theIntelCPU. Ablationstudy.WerunfourvariantsofAnsoronaconvo-
Baselines.WeincludePyTorch(v1.5)[39],Halideauto- lutionoperatorandreporttheperformancecurve.Wepickthe
scheduler (commit: 1f875b0) [2], FlexTensor (commit: lastconvolutionoperatorinResNet-50withbatchsize=16as
7ac302c) [59], and AutoTVM (commit: 69313a7) [12] as thetestcase,becauseitssearchspaceissufficientlylargeto
baselines.PyTorchisbackedbythevendor-providedkernel evaluatethesearchalgorithms.Otheroperatorsshareasim-
libraryMKL-DNN[27].Halideauto-schedulerisasequential ilarpattern.InFigure7,eachcurveisthemedianof5runs.
constructionbasedsearchframeworkforHalide.AutoTVM “Ansor (ours)” uses all our introduced techniques. “Beam
872 14th USENIX Symposium on Operating Systems Design and Implementation USENIX Association

Figure6:Singleoperatorperformancebenchmarkona20- Figure 8: Subgraph performance benchmark on a 20-core
core Intel-Platinum-8269CY. The y-axis is the throughput Intel-Platinum-8269CYandanNVIDIAV100."@C"denotes
normalizedtothebestthroughputforeachoperator. CPUresultsand"@G"denotesGPUresults. They-axisis
the throughput normalized to the best throughput for each
subgraph.
samesetofbaselineframeworksandrunthebenchmarkon
theIntelCPUandtheNVIDIAGPU.Wedonotreportthe
performanceofHalideauto-scheduleronGPUbecauseasof
writingthepaperitsGPUsupportisstillinanexperimental
stage.FlexTensorfailstorunoncomplicatedsubgraphslike
“TBS”.
Figure8showsthatAnsoroutperformsmanuallibraries
andothersearchframeworksby1.1 14.2 .Ansorcangen-
Figure7:AblationstudyoffourvariantsofAnsoronacon-  ⇥
eratehigh-performanceprogramsconsistentlyforthesesub-
volutionoperator.They-axisisthethroughputrelativetothe
graphsonbothplatforms.FlexTensorperformswellforsingle
throughputofthebestprogram.
operatorsbutshowslessadvantageforsubgraphsbecauseit
lacksthesupportofoperatorfusion.
Search”meanswepruneincompleteprogramswiththecost
modelduringthesamplingprocessanddonotusefine-tuning.
“Nofine-tuning”isbasedon“Ansor(ours)”butdisablesfine-
7.3 End-to-EndNetworkBenchmark
tuningandonlyreliesonrandomsampling.“Limitedspace”
isalsobasedon “Ansor(ours)”butlimitsthesearchspace Workloads.Webenchmarktheend-to-endinferenceexecu-
tomakeitsimilartothespaceinexistingmanualtemplates tion time of several DNNs,which include ResNet-50 [22]
(e.g.,limittilinglevel,innermosttilesizes,andcomputation andMobileNet-V2[43]forimageclassification,3D-ResNet-
location).AsdemonstratedbyFigure7,droppingeitherthe 18 [21] for action recognition,DCGAN [40] generator for
largesearchspaceorefficientfine-tuningdecreasesthefinal imagegeneration,andBERT[15]forlanguageunderstanding.
performance significantly. The aggressive early pruning in WebenchmarktheseDNNsonthreehardwareplatforms.For
“Beamsearch”throwsawayincompleteprogramswithgood theserver-classIntelCPUandNVIDIAGPU,wereportthe
finalperformanceduetoinaccurateestimation. resultsforbatchsize1andbatchsize16.FortheARMCPU
intheedgedevice,real-timefeedbackistypicallydesired,so
weonlyreporttheresultsforbatchsize1.
7.2 SubgraphBenchmark
Baselines and Settings. We include PyTorch (v1.5 with
Weperformthesubgraphbenchmarkontwocommonsub- torchscript),TensorFlow(v2.0withgraphmode),TensorRT
graphsinDNNs.The“ConvLayer”isasubgraphconsisting (v6.0 with TensorFlow integration) [38], TensorFlow Lite
of2Dconvolution,batchnormalization[28],andReLUac- (V2.0),andAutoTVMasbaselineframeworks.Wedonotin-
tivation,whichisacommonpatterninconvolutionalneural cludeHalideauto-schedulerorFlexTensorbecausetheylack
networks.The“TBS”isasubgraphconsistingoftwomatrix thesupportofwidely-useddeeplearningmodelformats(e.g.,
transposes,onebatchmatrixmultiplication,andasoftmax, ONNX,TensorFlowPB)andhigh-levelgraphoptimizations.
whichisapatterninthemulti-headattention[51]inlanguage Asaresult,weexpectthattheend-to-endexecutiontimethey
models.Similartothesingleoperatorbenchmark(§7.1),we canachievewillbethesumofthelatencyofallsubgraphsin
selectfourdifferentshapeconfigurationsandtwobatchsizes, aDNN.Incontract,AutoTVMcanoptimizeawholeDNN
runauto-tuningwithupto1,000measurementtrailspertest withitsmanualtemplatesandvariousgraph-leveloptimiza-
case, and report the normalized performance. We use the tions(e.g.,graph-levellayoutsearch[32],graph-levelconstant
USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation 873

(a)IntelCPU
Figure10:Networkperformanceauto-tuningcurve.They-
axisisthespeeduprelativetoAutoTVM.
NVIDIAGPUandARMCPU2.Overall,Ansorperformsthe
bestorequallythebestinallcases.Comparedwithsearch-
basedAutoTVM,Ansormatchesoroutperformsitinallcases
with1.0 21.8 speedup.Comparedwiththebestalterna-
 ⇥
tive,AnsorimprovestheexecutionperformanceofDNNson
theIntelCPU,ARMCPU,andNVIDIAGPUbyupto3.8 ,
⇥
2.6 ,and1.7 ,respectively.Thereasonforthesignificant
⇥ ⇥
speeduponDCGANisthatDCGANmainlyconsistsoftrans-
posed2Dconvolution(T2D),whichcanbewelloptimizedby
Ansor,asshownandexplainedinthesingleoperatorbench-
(b)NVIDIAGPU mark(§7.1).AutoTVMperformsverywellforResNet-50on
the IntelCPU thanks to its highly-optimizedtemplates for
2D convolution and global layout search [32]. Ansor does
notrunagloballayoutsearchbutdoesrewritethelayoutof
weighttensorsasdescribedin§4.2.Ansorusesmorelevels
oftilingsoitpacksweighttensorsintomorelevels.Thelay-
outrewritebringsabout40%improvementtoResNet-50in
Ansor.Comparedwithvendor-specificstaticlibraries,Ansor
hasmoreadvantagesonuncommonshapesandsmallbatch
sizes,becauseitisnoteasytomanuallyoptimizeforthese
(c)ARMCPU
Figure9:Networkinferenceperformancebenchmarkonthree cases.
hardwareplatforms.They-axisisthethroughputrelativeto Ablationstudy.WerunvariantsofAnsorontwotestcases
thebestthroughputforeachnetwork. inFigure10.Intheleftfigure,werunfourvariantsofAnsorto
generateprogramsforasinglemobilenet-V2.Intherightfig-
ure,werunthesevariantsforbothmobilenet-V2andResNet-
50.Wesettheobjectivefunctionofthetaskschedulertobethe
folding[42])whichimprovetheperformancesignificantly.
geometricmeanofspeedupagainstAutoTVM.Asshownin
Ansoralsoperformslayoutrewriteasdescribedin§4.2.We
Figure10,“Notaskscheduler”meansweusearound-robin
letbothAutoTVMandAnsorrunauto-tuninguntiltheyuse
strategy to allocate equal time resources to all subgraphs.
to1000 nmeasurementtrialsoneachDNN,wherenisthe
⇥ “Limited space” is based on “Ansor (ours)” but limits the
numberofsubgraphsintheDNN.Thisistypicallyenoughfor
searchspace.“Nofine-tuning”isalsobasedon“Ansor(ours)”
themtoconverge.Wesettheobjectiveofthetaskscheduler
butdisablesfine-tuningandreliesonrandomsamplingonly.
as minimizing the total latency of one DNN and generate
AscanbeseeninFigure10,“Limitedspace”performsthe
programsforthesenetworksonebyone.Ontheotherhand,
worstintermsofthefinalachievedperformance,provingthat
PyTorch,TensorFlow,TensorRT,andTensorFlowLiteareall
thebestprogramsarenotincludedinthelimitedspace.The
backedbystatickernellibraries(MKL-DNNonIntelCPU,
finalachievedperformancecanbeimprovedbyenlargingthe
CuDNNonNVIDIAGPU,andEigenonARMCPU)anddo
searchspace,asdepictedin“Nofine-tuning”. However,in
notneedauto-tuning.WeenableAVX-512forallframeworks
therightfigure,randomlyassigningtilesizesandannotations
ontheIntelCPUinthisnetworkbenchmark.
23D-ResNetandDCGANarenotyetsupportedbyTensorFlowLiteon
Results. Figure 9 shows the results on the Intel CPU, theARMCPU.
874 14th USENIX Symposium on Operating Systems Design and Implementation USENIX Association

stillcannotbeatAutoTVMinthegiventimebudget. After AutoTVM Ansor Time-saving
enablingfine-tuning,“Notaskscheduler”outperformsAu- ResNet-50 21,220 6,403 3.3
⇥
toTVM in both cases. Finally,“Ansor(ours)” employs the Mobilenet-V2 31,272 1,892 16.5
⇥
taskschedulertoprioritizeperformancebottlenecks(e.g.,sub- 3D-ResNet 5,158 1,927 2.7
⇥
graphscontain3x3convolution),soitperformsthebestin DCGAN 3,003 298 10.1
⇥
bothsearchefficiencyandthefinalachievedperformance. BERT 6,220 496 12.5
⇥
(a)Thenumberofmeasurements.
7.4 SearchTime
AutoTVM Ansor Time-saving
AnsorsearchesefficientlyandcanoutperformormatchAu- ResNet-50 39,250 4,540 8.6
⇥
toTVMwithlesssearchtime.Ansorslicesthetimeanduti- Mobilenet-V2 58,468 660 88.6
⇥
lizesthetaskschedulertosimultaneouslyoptimizeallsub- 3D-ResNet 7,594 2,296 3.3
⇥
graphstogether.Incontrast,AutoTVMandothersystemsdo DCGAN 4,914 420 11.7
⇥
nothaveataskscheduler,sotheygenerateprogramsforall BERT 12,007 266 45.1
⇥
subgraphsonebyonewithapredefinedbudgetofmeasure- (b)Wall-clocktime(seconds)
menttrialsforeachsubgraph. Ansorsavesthesearchtime
byprioritizingimportantsubgraphs,whileAutoTVMspends Table3:Thenumberofmeasurementsandwall-clocktime
predefinedtimebudgetoneverysubgraph,whichmaybea usedforAnsortomatchtheperformanceofAutoTVMonthe
wasteontheunimportantsubgraphs. IntelCPU(batchsize=1).
Table3showsthesearchtimerequiredforAnsortomatch
the performance of AutoTVM on the Intel CPU network
benchmark (§7.3). We list the search time in two metrics:
numberofmeasurementsandwall-clocktime.“Numberof
measurements” is a metric agnostic to the implementation
ofmeasurementandtheoverheadofsearchalgorithm,while
“Wall-clocktime”takesthesefactorsintoaccount.Asshown
inthetable,AnsorcanmatchtheperformanceofAutoTVM
withanorderofmagnitudelesssearchtime.InTable3athe
saving in search time comes from the task scheduler, effi-
cientfine-tuning,andcomprehensive coverage ofeffective
Figure11:Measuredthroughputsvs.predictedthroughputs.
optimizations.InTable3b,Ansorshowsmoretime-saving
thebestperformingprogramsinthetestset.Thepredicted
inwall-clocktime.ThisisbecauseAnsordoesnotintroduce
throughputsaretheoutputofthemodel,sotheycanbeneg-
muchsearchoverheadandhasabetterimplementationofthe
ative. In Figure11a,thepointsscatteraroundthediagonal
measurement(ontheIntelCPU,Ansorcangetaccuratemea-
line,meaningthatthemodelmakesaccuratepredictions.The
surementresultswithfewerrepetitionsbyexplicitlyflushing
distributionisnotuniformbecausethedatasetiscollected
thecacheforsometensors).Onotherbackends,Ansorcan
duringthesearch.Goodprogramshaveahigherprobability
matchtheperformanceofAutoTVMwithasimilarsavingin
tobechosenformeasurements,somostoftheprogramsare
searchtime.
in the top right corner. The points with measured through-
Typically,ittakesseveralhoursforAnsortogeneratefully-
put0.0areprogramsthatareinvalidorkilledduetotimeout
optimizedprogramsforaDNNonasinglemachine.Thisis
duringmeasurements.InFigure11b,wesortthe5000points
acceptableforinferenceapplicationsbecauseitisaone-shot
accordingtothepredictionsfromtheslowesttothefastest,
effortbeforedeployment.Inaddition,thewholearchitecture
andusetherelativerankingasx-axis.Sothepointsaredis-
ofAnsorcanbeparallelizedveryeasily.
tributeduniformlyoverx-axis. Itshows the distribution of
performanceoftheexploredprogramsbetter.
7.5 CostModelEvaluation The model archives 0.079 RMSE, 0.958 R2 correlation,
0.851pairwisecomparisonaccuracy,and0.624recall@30of
Inthissubsection,weevaluatethepredictionqualityofthe
top-30programs(seethedefinitionatfootnote1)onthetest
learnedcostmodel.Weuse25,000programsmeasureddur-
set.
ingtuningResNet-50ontheIntelCPUasthedataset.We
randomlypick20,000programsasthetrainingsetanduse
theremaining5,000programsasthetestset.Wetrainthecost 8 RelatedWork
modelandletitmakepredictionsforthetestset.
Figure 11 plots the predicted throughputs vs. measured Automatic tensor program generation based on schedul-
throughputs. The measured throughputs are normalized to inglanguages.Halide[41]introducesaschedulinglanguage
USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation 875

thatcandescribeloopoptimizationprimitives.Thislanguage searchspaceautomatically.Traditionalhigh-performanceli-
issuitableforbothmanualoptimizationandautomaticsearch. braries such as ATLAS [56] and FFTW [16] also utilize
Halidehasthreeversionsofauto-schedulerbasedondiffer- auto-tuning. More recent works NeuroVectorizer [18] and
enttechniques[2,31,36]. Thelatestonewithbeamsearch AutoPhase [20,26] use deep reinforcement learning to au-
andlearnedcostmodelperformsthebestamongthem,which tomatically vectorize programs and optimize the compiler
| is also usedin | ourevaluation. |     | TVM [11] | utilizes | a similar | phaseordering. |     |     |     |     |     |     |
| -------------- | -------------- | --- | -------- | -------- | --------- | -------------- | --- | --- | --- | --- | --- | --- |
schedulinglanguageandincludesatemplate-guidedsearch
frameworkAutoTVM[12].FlexTensor[59]proposesgeneral
9 LimitationsandFuturework
templatesthatcantargetasetofoperators,butitstemplates
aredesignedforsingleoperators.Itishardtousethesetem-
|     |     |     |     |     |     | One of Ansor’s | limitations |     | is  | that Ansor | cannot | optimize |
| --- | --- | --- | --- | --- | --- | -------------- | ----------- | --- | --- | ---------- | ------ | -------- |
platesforoptimizationsinvolvingmultipleoperators(e.g.,op-
graphswithdynamicshapes[45].Ansorrequirestheshapes
eratorfusion).AconcurrentworkProTuner[19]usesMonte
|     |     |     |     |     |     | in the computational |     | graph | to  | be static | and known | in ad- |
| --- | --- | --- | --- | --- | --- | -------------------- | --- | ----- | --- | --------- | --------- | ------ |
Carlo tree search to solve the inaccurate estimation prob- vancetodoanalysis,constructthesearchspace,andperform
| lem in Halide | auto-scheduler. |     | ProTunermainly |     | targets im- |               |     |     |          |          |             |     |
| ------------- | --------------- | --- | -------------- | --- | ----------- | ------------- | --- | --- | -------- | -------- | ----------- | --- |
|               |                 |     |                |     |             | measurements. | How | to  | generate | programs | forsymbolic | or  |
ageprocessingworkloads,whileAnsortargetsdeeplearning
|     |     |     |     |     |     | dynamic | shape is | an interesting |     | future direction. |     | Another |
| --- | --- | --- | --- | --- | --- | ------- | -------- | -------------- | --- | ----------------- | --- | ------- |
workloadsandintroducesnewsearchspaceandotheropti-
|     |     |     |     |     |     | limitation | is that | Ansor | only supports | dense | operators. | To  |
| --- | --- | --- | --- | --- | --- | ---------- | ------- | ----- | ------------- | ----- | ---------- | --- |
mizations.
|     |     |     |     |     |     | support | sparse operators |     | (e.g.,SpMM) | that | are | commonly |
| --- | --- | --- | --- | --- | --- | ------- | ---------------- | --- | ----------- | ---- | --- | -------- |
Polyhedralcompilationmodels.Thepolyhedralcompila- used in sparse neural networks [17] and graph neural net-
tionmodel[8,52,53]formulatestheoptimizationofprograms
works[25],weexpectthatalargeportionofAnsorcanstill
asanintegerlinearprogramming(ILP)problem.Itoptimizes bereused,butweneedtoredesignthesearchspace.Lastly,
aprogramwithaffinelooptransformationthatminimizesthe
Ansoronlyperformsprogramoptimizationsatahighlevelbut
datareusedistancebetweendependentstatements.Tiramisu
reliesonothercodegenerators(e.g.,LLVMandNVCC)to
[5]andTensorComprehensions[49]aretwopolyhedralcom- doplatform-dependentoptimizations(e.g.,instructionselec-
pilersthatalsotargetthedeeplearningdomain.Tiramisupro-
tion).Ansorcomesshortofutilizingthespecialinstructions,
videsaschedulinglanguagesimilartotheHalidelanguage, suchasIntelVNNI,NVIDIATensorCore,andARMDotfor
anditneedsmanualscheduling.TensorComprehensionscan mixed-precisionandlow-precisionoperators,whicharenot
searchforGPUcodeautomatically,butitisnotyetmeantto
handledwellbytheoff-the-shelfcodegeneratorscurrently.
beusedforcompute-boundedproblems[11].Itcannotoutper-
formTVMonoperatorslikeconv2dandmatmul[11,48].This
10 Conclusion
isbecauseofthelackofcertainoptimizations[50]andthe
inaccurateimplicitcostmodelinthepolyhedralformulation.
|     |     |     |     |     |     | We propose | Ansor, | an  | automated | search | framework | that |
| --- | --- | --- | --- | --- | --- | ---------- | ------ | --- | --------- | ------ | --------- | ---- |
Graph-leveloptimizationfordeeplearning.Graph-level
|               |          |            |                   |     |       | generates     | high-performance |             | tensorprograms |         | fordeep | neu-  |
| ------------- | -------- | ---------- | ----------------- | --- | ----- | ------------- | ---------------- | ----------- | -------------- | ------- | ------- | ----- |
| optimizations | treat an | operatorin | the computational |     | graph |               |                  |             |                |         |         |       |
|               |          |            |                   |     |       | ral networks. | By               | efficiently | exploring      | a large | search  | space |
asabasicunitandperformoptimizationatgraphlevelwith-
andprioritizingperformancebottlenecks,Ansorfindshigh-
outchangingtheinternalimplementationsofoperators.The
|     |     |     |     |     |     | performance | programs |     | thatare | outside the | searchspace | of  |
| --- | --- | --- | --- | --- | --- | ----------- | -------- | --- | ------- | ----------- | ----------- | --- |
commonoptimizationsatgraphlevelincludelayoutoptimiza-
existingapproaches.Ansoroutperformsexistingmanualli-
| tions[32],operatorfusion[11,38,60],constantfolding |     |     |     |     | [42], |     |     |     |     |     |     |     |
| -------------------------------------------------- | --- | --- | --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- |
brariesandsearch-basedframeworksonadiversesetofneural
| auto-batching                                          | [33],automaticgenerationofgraphsubstitu- |     |     |     |     |                                       |     |     |     |     |             |     |
| ------------------------------------------------------ | ---------------------------------------- | --- | --- | --- | --- | ------------------------------------- | --- | --- | --- | --- | ----------- | --- |
|                                                        |                                          |     |     |     |     | networksandhardwareplatformsbyupto3.8 |     |     |     |     | .Byautomat- |     |
| tion [29]andsoforth.Thegraph-leveloptimizationsaretyp- |                                          |     |     |     |     |                                       |     |     |     |     | ⇥           |     |
icallysearchingforbetterprograms,wehopethatAnsorwill
icallycomplementarytooperator-leveloptimizations.Graph-
helpbridgethegapbetweentheincreasingdemandincom-
leveloptimizationscanalsobenefitfromhigh-performance
|     |     |     |     |     |     | puting power | and | limited | hardware | performance. |     | Ansor is |
| --- | --- | --- | --- | --- | --- | ------------ | --- | ------- | -------- | ------------ | --- | -------- |
implementations of operators. Forexample,general opera- integratedintotheApacheTVMopen-sourceproject3.
torfusionreliesonthecodegenerationabilityofAnsor.We
leavethejointoptimizationofAnsorandmoregraph-level
11 Acknowledgement
optimizationasfuturework.
Search
| Search-based | compilation |     | and auto-tuning. |     |     |     |     |     |     |     |     |     |
| ------------ | ----------- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
WewouldliketothankWeizhaoXian,TianqiChen,Frank
basedcompilationandauto-tuninghavealreadyshowntheir
Luan,anonymousreviewers,andourshepherd,DerekMur-
| effectiveness | in domains      | other | than deep | learning. | Stock |                                 |     |     |     |                     |     |     |
| ------------- | --------------- | ----- | --------- | --------- | ----- | ------------------------------- | --- | --- | --- | ------------------- | --- | --- |
|               |                 |       |           |           |       | ray,fortheirinsightfulfeedback. |     |     |     | InadditiontoNSFCISE |     |     |
| [44] is a     | super-optimizer | based | on random | search.   | Stock |                                 |     |     |     |                     |     |     |
ExpeditionsAwardCCF-1730628,thisresearchissupported
searchesforloop-freehardwareinstructionsequences,while
|     |     |     |     |     |     | by gifts | from Alibaba | Group,Amazon |     | Web | Services,Ant |     |
| --- | --- | --- | --- | --- | --- | -------- | ------------ | ------------ | --- | --- | ------------ | --- |
Ansorgeneratestensorprogramswithnestsofloops.Open-
Group,CapitalOne,Ericsson,Facebook,Futurewei,Google,
| Tuner [4] | is a general | framework | for program |     | auto-tuning |     |     |     |     |     |     |     |
| --------- | ------------ | --------- | ----------- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- |
Intel,Microsoft,Nvidia,Scotiabank,Splunk,andVMware.
basedonmulti-armedbanditapproaches.OpenTunerrelies
on user-specified search space,while Ansorconstructs the 3https://tvm.apache.org/
876    14th USENIX Symposium on Operating Systems Design and Implementation USENIX Association

| References |     |     |     |     |     |     | [10] TianqiChen,MuLi,YutianLi,MinLin,NaiyanWang, |     |     |     |     |     |
| ---------- | --- | --- | --- | --- | --- | --- | ------------------------------------------------ | --- | --- | --- | --- | --- |
MinjieWang,TianjunXiao,BingXu,ChiyuanZhang,
| [1] Martín | Abadi, | Paul Barham, | Jianmin | Chen, |     | Zhifeng |                |     |                                |     |     |     |
| ---------- | ------ | ------------ | ------- | ----- | --- | ------- | -------------- | --- | ------------------------------ | --- | --- | --- |
|            |        |              |         |       |     |         | andZhengZhang. |     | Mxnet:aflexibleandefficientma- |     |     |     |
Chen,AndyDavis,JeffreyDean,MatthieuDevin,San- chinelearninglibraryforheterogeneousdistributedsys-
| jay Ghemawat, |     | Geoffrey | Irving, | Michael | Isard, | et al. |       |                                     |     |     |     |     |
| ------------- | --- | -------- | ------- | ------- | ------ | ------ | ----- | ----------------------------------- | --- | --- | --- | --- |
|               |     |          |         |         |        |        | tems. | arXivpreprintarXiv:1512.01274,2015. |     |     |     |     |
Tensorflow:asystemforlarge-scalemachinelearning.
|     |     |     |     |     |     |     | [11] TianqiChen,ThierryMoreau,ZihengJiang,Lianmin |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------------------------------------- | --- | --- | --- | --- | --- |
In12thUSENIXSymposiumonOperatingSystemsDe-
sign and Implementation (OSDI 16),pages 265–283, Zheng, Eddie Yan, Haichen Shen, Meghan Cowan,
LeyuanWang,YuweiHu,LuisCeze,etal.Tvm:anauto-
2016.
matedend-to-endoptimizingcompilerfordeeplearning.
[2] AndrewAdams,KarimaMa,LukeAnderson,Riyadh In13thUSENIXSymposiumonOperatingSystemsDe-
Baghdadi,Tzu-MaoLi,MichaëlGharbi,BenoitSteiner, sign and Implementation (OSDI 18),pages 578–594,
| StevenJohnson,KayvonFatahalian,FrédoDurand,etal. |             |        |      |             |     |          | 2018. |     |     |     |     |     |
| ------------------------------------------------ | ----------- | ------ | ---- | ----------- | --- | -------- | ----- | --- | --- | --- | --- | --- |
| Learning                                         | to optimize | halide | with | tree search |     | and ran- |       |     |     |     |     |     |
domprograms. ACMTransactionsonGraphics(TOG), [12] TianqiChen,LianminZheng,EddieYan,ZihengJiang,
ThierryMoreau,LuisCeze,CarlosGuestrin,andArvind
38(4):1–12,2019.
|     |     |     |     |     |     |     | Krishnamurthy. |     | Learningtooptimizetensorprograms. |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------------- | --- | --------------------------------- | --- | --- | --- |
[3] Hassan Abu Alhaija,Siva Karthik Mustikovela,Lars InAdvancesinNeuralInformationProcessingSystems,
Mescheder,AndreasGeiger,andCarstenRother. Aug- pages3389–3400,2018.
mentedrealitymeetsdeeplearningforcarinstanceseg-
|                         |     |     |                        |     |     |     | [13] SharanChetlur,CliffWoolley,PhilippeVandermersch, |     |     |     |     |     |
| ----------------------- | --- | --- | ---------------------- | --- | --- | --- | ----------------------------------------------------- | --- | --- | --- | --- | --- |
| mentationinurbanscenes. |     |     | InBritishmachinevision |     |     |     |                                                       |     |     |     |     |     |
JonathanCohen,JohnTran,BryanCatanzaro,andEvan
conference,volume1,page2,2017.
|     |     |     |     |     |     |     | Shelhamer. |     | cudnn:efficientprimitivesfordeeplearning. |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---------- | --- | ----------------------------------------- | --- | --- | --- |
[4] Jason Ansel,Shoaib Kamil,Kalyan Veeramachaneni, arXivpreprintarXiv:1410.0759,2014.
| Jonathan                      | Ragan-Kelley, |     | Jeffrey | Bosboom,        | Una-May |     |             |         |         |                  |     |        |
| ----------------------------- | ------------- | --- | ------- | --------------- | ------- | --- | ----------- | ------- | ------- | ---------------- | --- | ------ |
|                               |               |     |         |                 |         |     | [14] Marius | Cordts, | Mohamed | Omran, Sebastian |     | Ramos, |
| O’Reilly,andSamanAmarasinghe. |               |     |         | Opentuner:anex- |         |     |             |         |         |                  |     |        |
TimoRehfeld,MarkusEnzweiler,RodrigoBenenson,
| tensibleframeworkforprogramautotuning. |          |               |            |     | InProceed- |          |     |         |        |                 |          |     |
| -------------------------------------- | -------- | ------------- | ---------- | --- | ---------- | -------- | --- | ------- | ------ | --------------- | -------- | --- |
|                                        |          |               |            |     |            |          | Uwe | Franke, | Stefan | Roth, and Bernt | Schiele. | The |
| ings of                                | the 23rd | international | conference |     | on         | Parallel |     |         |        |                 |          |     |
cityscapesdatasetforsemanticurbansceneunderstand-
architecturesandcompilation,pages303–316,2014.
ing.InProceedingsoftheIEEEconferenceoncomputer
[5] RiyadhBaghdadi,JessicaRay,MalekBenRomdhane, visionandpatternrecognition,pages3213–3223,2016.
EmanueleDelSozzo,AbdurrahmanAkkas,Yunming
|     |     |     |     |     |     |     | [15] Jacob | Devlin, | Ming-Wei | Chang, Kenton | Lee, | and |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ------- | -------- | ------------- | ---- | --- |
Zhang,PatriciaSuriana,ShoaibKamil,andSamanAma-
|     |     |     |     |     |     |     | KristinaToutanova. |     | Bert:pre-trainingofdeepbidirec- |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | ------------------------------- | --- | --- | --- |
rasinghe. Tiramisu:apolyhedralcompilerforexpress- tionaltransformersforlanguageunderstanding. arXiv
| ingfastandportablecode. |     |     | In2019IEEE/ACMInterna- |     |     |     |     |     |     |     |     |     |
| ----------------------- | --- | --- | ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
preprintarXiv:1810.04805,2018.
tionalSymposiumonCodeGenerationandOptimiza-
tion(CGO),pages193–205.IEEE,2019. [16] Matteo Frigo and Steven G Johnson. Fftw: an adap-
|     |     |     |     |     |     |     | tive | software | architecture | for the fft. | In Proceedings |     |
| --- | --- | --- | --- | --- | --- | --- | ---- | -------- | ------------ | ------------ | -------------- | --- |
[6] JunjieBai,FangLu,KeZhang,etal. Onnx:openneural ofthe1998IEEEInternationalConferenceonAcous-
networkexchange,2019.
tics,SpeechandSignalProcessing,ICASSP’98(Cat.No.
98CH36181),volume3,pages1381–1384.IEEE,1998.
| [7] PaulBarhamandMichaelIsard. |     |     |     | Machinelearningsys- |     |     |     |     |     |     |     |     |
| ------------------------------ | --- | --- | --- | ------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
temsarestuckinarut. InProceedingsoftheWorkshop [17] TrevorGale,ErichElsen,andSaraHooker. Thestate
on Hot Topics in Operating Systems,pages 177–183, of sparsity in deep neural networks. arXiv preprint
2019.
arXiv:1902.09574,2019.
| [8] Uday Bondhugula, |     | Albert | Hartono, | Jagannathan |     | Ra- |            |          |         |          |     |         |
| -------------------- | --- | ------ | -------- | ----------- | --- | --- | ---------- | -------- | ------- | -------- | --- | ------- |
|                      |     |        |          |             |     |     | [18] Ameer | Haj-Ali, | Nesreen | K Ahmed, | Ted | Willke, |
manujam,andPonnuswamySadayappan. Apractical Yakun Sophia Shao, Krste Asanovic, and Ion Stoica.
automaticpolyhedralparallelizerandlocalityoptimizer. Neurovectorizer: end-to-end vectorization with deep
InProceedingsofthe29thACMSIGPLANConference reinforcement learning. In Proceedings of the 18th
onProgrammingLanguageDesignandImplementation, ACM/IEEEInternationalSymposiumonCodeGenera-
pages101–113,2008.
tionandOptimization,pages242–255,2020.
[9] TianqiChenandCarlosGuestrin. Xgboost:ascalable [19] Ameer Haj-Ali, Hasan Genc, Qijing Huang, William
treeboostingsystem. InProceedingsofthe22ndacm Moses,JohnWawrzynek,KrsteAsanovic´,andIonSto-
sigkddinternationalconferenceonknowledgediscovery ica. Protuner: tuningprogramswithmontecarlotree
anddatamining,pages785–794,2016. search. arXivpreprintarXiv:2005.13685,2020.
USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation    877

[20] Ameer Haj-Ali, Qijing Huang, William Moses, John [30] AndrewLavinandScottGray. Fastalgorithmsforcon-
Xiang,JohnWawrzynek,KrsteAsanovic,andIonSto- volutionalneuralnetworks. InProceedingsoftheIEEE
ica. Autophase:jugglinghlsphaseorderingsinrandom ConferenceonComputerVisionandPatternRecogni-
forestswithdeepreinforcementlearning. InThirdCon- tion,pages4013–4021,2016.
| ference | on  | Machine | Learning | and Systems | (ML-Sys), |     |              |     |                         |     |     |             |     |
| ------- | --- | ------- | -------- | ----------- | --------- | --- | ------------ | --- | ----------------------- | --- | --- | ----------- | --- |
|         |     |         |          |             |           |     | [31] Tzu-Mao |     | Li,MichaëlGharbi,Andrew |     |     | Adams,Frédo |     |
2020.
|     |     |     |     |     |     |     | Durand, |     | and Jonathan | Ragan-Kelley. |     | Differentiable |     |
| --- | --- | --- | --- | --- | --- | --- | ------- | --- | ------------ | ------------- | --- | -------------- | --- |
programmingforimageprocessinganddeeplearning
| [21] Kensho      | Hara,          | Hirokatsu      | Kataoka,                   | and     | Yutaka      | Satoh. |                                                |         |     |              |     |          |        |
| ---------------- | -------------- | -------------- | -------------------------- | ------- | ----------- | ------ | ---------------------------------------------- | ------- | --- | ------------ | --- | -------- | ------ |
|                  |                |                |                            |         |             |        | in                                             | halide. | ACM | Transactions | on  | Graphics | (TOG), |
| Can              | spatiotemporal | 3d             | cnns retrace               |         | the history | of 2d  |                                                |         |     |              |     |          |        |
| cnnsandimagenet? |                |                | InProceedingsoftheIEEECon- |         |             |        | 37(4):139,2018.                                |         |     |              |     |          |        |
| ference          | on             | ComputerVision | and                        | Pattern | Recognition |        |                                                |         |     |              |     |          |        |
|                  |                |                |                            |         |             |        | [32] YizhiLiu,YaoWang,RuofeiYu,MuLi,VinSharma, |         |     |              |     |          |        |
(CVPR),pages6546–6555,2018.
|     |     |     |     |     |     |     | andYida |                                       | Wang. | Optimizing | cnn modelinference |     | on  |
| --- | --- | --- | --- | --- | --- | --- | ------- | ------------------------------------- | ----- | ---------- | ------------------ | --- | --- |
|     |     |     |     |     |     |     | cpus.   | In2019USENIXAnnualTechnicalConference |       |            |                    |     |     |
[22] KaimingHe,XiangyuZhang,ShaoqingRen,andJian
(USENIXATC19),pages1025–1040,2019.
| Sun. | Deepresiduallearningforimagerecognition. |     |     |     |     | In  |     |     |     |     |     |     |     |
| ---- | ---------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ProceedingsoftheIEEEconferenceoncomputervision
|     |     |     |     |     |     |     | [33] MosheLooks,MarcelloHerreshoff,DeLesleyHutchins, |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---------------------------------------------------- | --- | --- | --- | --- | --- | --- |
andpatternrecognition,pages770–778,2016. andPeterNorvig. Deeplearningwithdynamiccompu-
|     |     |     |     |     |     |     | tationgraphs. |     | arXivpreprintarXiv:1702.02181,2017. |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------- | --- | ----------------------------------- | --- | --- | --- | --- |
[23] GeoffreyEHinton,SaraSabour,andNicholasFrosst.
Matrixcapsuleswithemrouting. 2018. [34] Mark F. Medress,Franklin S Cooper,Jim W. Forgie,
CCGreen,DennisH.Klatt,MichaelH.O’Malley,Ed-
wardPNeuburg,AllenNewell,DRReddy,BRitea,etal.
[24] AndrewGHoward,MenglongZhu,BoChen,Dmitry
Kalenichenko,Weijun Wang,Tobias Weyand,Marco Speechunderstandingsystems:reportofasteeringcom-
Andreetto,and Hartwig Adam. Mobilenets: efficient mittee. ArtificialIntelligence,9(3):307–316,1977.
convolutionalneuralnetworksformobilevisionappli-
|          |                                     |     |     |     |     |     | [35] ThierryMoreau,TianqiChen,LuisVega,JaredRoesch, |     |     |     |     |     |     |
| -------- | ----------------------------------- | --- | --- | --- | --- | --- | --------------------------------------------------- | --- | --- | --- | --- | --- | --- |
| cations. | arXivpreprintarXiv:1704.04861,2017. |     |     |     |     |     |                                                     |     |     |     |     |     |     |
EddieYan,LianminZheng,JoshFromm,ZihengJiang,
|     |     |     |     |     |     |     | LuisCeze,CarlosGuestrin,etal. |     |     |     | Ahardware–software |     |     |
| --- | --- | --- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | ------------------ | --- | --- |
[25] YuweiHu,ZihaoYe,MinjieWang,JialiYu,DaZheng,
|     |           |        |              |     |          |       | blueprintforflexibledeeplearningspecialization. |     |     |     |     |     | IEEE |
| --- | --------- | ------ | ------------ | --- | -------- | ----- | ----------------------------------------------- | --- | --- | --- | --- | --- | ---- |
| Mu  | Li, Zheng | Zhang, | Zhiru Zhang, |     | and Yida | Wang. |                                                 |     |     |     |     |     |      |
Featgraph: A flexible and efficient backend for Micro,39(5):8–16,2019.
| graph | neural | network | systems. |     | arXiv preprint |     |                                           |     |     |     |     |     |          |
| ----- | ------ | ------- | -------- | --- | -------------- | --- | ----------------------------------------- | --- | --- | --- | --- | --- | -------- |
|       |        |         |          |     |                |     | [36] RaviTejaMullapudi,AndrewAdams,Dillon |     |     |     |     |     | Sharlet, |
arXiv:2008.11359,2020.
|     |     |     |     |     |     |     | JonathanRagan-Kelley,andKayvonFatahalian. |     |     |     |     |     | Auto- |
| --- | --- | --- | --- | --- | --- | --- | ----------------------------------------- | --- | --- | --- | --- | --- | ----- |
maticallyschedulinghalideimageprocessingpipelines.
[26] QijingHuang,AmeerHaj-Ali,WilliamMoses,JohnXi-
ACMTransactionsonGraphics(TOG),35(4):83,2016.
ang,IonStoica,KrsteAsanovic,andJohnWawrzynek.
Autophase:compilerphase-orderingforhlswithdeep [37] Nvidia. Nvidiatensorcores,2017.
| reinforcementlearning. |     |     | In2019IEEE27thAnnualIn- |     |     |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | ----------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ternationalSymposiumonField-ProgrammableCustom [38] Nvidia. Nvidiatensorrt:programmableinferenceaccel-
erator,2017.
ComputingMachines(FCCM),pages308–308.IEEE,
2019.
|     |     |     |     |     |     |     | [39] Adam | Paszke, | Sam | Gross, | Francisco | Massa, | Adam |
| --- | --- | --- | --- | --- | --- | --- | --------- | ------- | --- | ------ | --------- | ------ | ---- |
Lerer,JamesBradbury,GregoryChanan,TrevorKilleen,
| [27] Intel. | IntelR | mathkernellibraryfordeeplearningnet- |     |     |     |     |        |     |              |             |     |              |        |
| ----------- | ------ | ------------------------------------ | --- | --- | --- | --- | ------ | --- | ------------ | ----------- | --- | ------------ | ------ |
|             |        |                                     |     |     |     |     | Zeming |     | Lin, Natalia | Gimelshein, |     | Luca Antiga, | et al. |
works,2017.
|                                      |     |     |     |     |                 |     | Pytorch: |     | an imperative | style,      | high-performance |             | deep |
| ------------------------------------ | --- | --- | --- | --- | --------------- | --- | -------- | --- | ------------- | ----------- | ---------------- | ----------- | ---- |
|                                      |     |     |     |     |                 |     | learning |     | library.      | In Advances | in Neural        | Information |      |
| [28] SergeyIoffeandChristianSzegedy. |     |     |     |     | Batchnormaliza- |     |          |     |               |             |                  |             |      |
ProcessingSystems,pages8024–8035,2019.
tion:acceleratingdeepnetworktrainingbyreducingin-
ternalcovariateshift. arXivpreprintarXiv:1502.03167, [40] AlecRadford,LukeMetz,andSoumithChintala. Un-
2015.
supervisedrepresentationlearningwithdeepconvolu-
|     |     |     |     |     |     |     | tionalgenerativeadversarialnetworks. |     |     |     |     | arXivpreprint |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------------------------ | --- | --- | --- | --- | ------------- | --- |
[29] ZhihaoJia,OdedPadon,JamesThomas,ToddWarsza- arXiv:1511.06434,2015.
| wski,MateiZaharia,andAlexAiken. |     |     |     |     | Taso:optimizing |     |     |     |     |     |     |     |     |
| ------------------------------- | --- | --- | --- | --- | --------------- | --- | --- | --- | --- | --- | --- | --- | --- |
deeplearningcomputationwithautomaticgeneration [41] Jonathan Ragan-Kelley, Connelly Barnes, Andrew
ofgraphsubstitutions. InProceedingsofthe27thACM Adams,SylvainParis,FrédoDurand,andSamanAma-
SymposiumonOperatingSystemsPrinciples,pages47– rasinghe. Halide:alanguageandcompilerforoptimiz-
| 62,2019. |     |     |     |     |     |     | ing | parallelism,locality,and |     |     | recomputation |     | in image |
| -------- | --- | --- | --- | --- | --- | --- | --- | ------------------------ | --- | --- | ------------- | --- | -------- |
878    14th USENIX Symposium on Operating Systems Design and Implementation USENIX Association

processingpipelines. AcmSigplanNotices,48(6):519– [51] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob
| 530,2013.               |     |     |                    |     |     |           | Uszkoreit,LlionJones,AidanNGomez,ŁukaszKaiser, |     |                        |     |     |       |
| ----------------------- | --- | --- | ------------------ | --- | --- | --------- | ---------------------------------------------- | --- | ---------------------- | --- | --- | ----- |
|                         |     |     |                    |     |     |           | andIlliaPolosukhin.                            |     | Attentionisallyouneed. |     |     | InAd- |
| [42] JaredRoesch,Steven |     |     | Lyubomirsky,Marisa |     |     | Kirisame, |                                                |     |                        |     |     |       |
vancesinneuralinformationprocessingsystems,pages
JoshPollock,LoganWeber,ZihengJiang,TianqiChen,
5998–6008,2017.
| ThierryMoreau,andZacharyTatlock. |     |     |     |     | Relay: | ahigh-   |     |     |     |     |     |     |
| -------------------------------- | --- | --- | --- | --- | ------ | -------- | --- | --- | --- | --- | --- | --- |
|                                  |     |     |     |     | arXiv  | preprint |     |     |     |     |     |     |
level compiler for deep learning. [52] SvenVerdoolaege. Presburgerformulasandpolyhedral
| arXiv:1904.08368,2019. |     |     |     |     |     |     | compilation. | 2016. |     |     |     |     |
| ---------------------- | --- | --- | --- | --- | --- | --- | ------------ | ----- | --- | --- | --- | --- |
[43] MarkSandler,AndrewHoward,MenglongZhu,Andrey [53] Sven Verdoolaege, Juan Carlos Juega, Albert Cohen,
Zhmoginov,andLiang-ChiehChen. Mobilenetv2:in- JoseIgnacioGomez,ChristianTenllado,andFrancky
vertedresidualsandlinearbottlenecks. InProceedings Catthoor. Polyhedralparallelcodegenerationforcuda.
oftheIEEEconferenceoncomputervisionandpattern ACMTransactionsonArchitectureandCodeOptimiza-
recognition,pages4510–4520,2018.
tion(TACO),9(4):1–23,2013.
| [44] EricSchkufza,RahulSharma,andAlexAiken. |     |     |     |     |     | Stochas- |                 |     |                                  |     |     |     |
| ------------------------------------------- | --- | --- | --- | --- | --- | -------- | --------------- | --- | -------------------------------- | --- | --- | --- |
|                                             |     |     |     |     |     | [54]     | PradnyaAVikhar. |     | Evolutionaryalgorithms:acritical |     |     |     |
ticsuperoptimization. ACMSIGARCHComputerArchi- reviewanditsfutureprospects. In2016International
tectureNews,41(1):305–316,2013. conferenceonglobaltrendsinsignalprocessing,infor-
mationcomputingandcommunication(ICGTSPICC),
| [45] Haichen | Shen, | Jared | Roesch, | Zhi | Chen, Wei | Chen, |     |     |     |     |     |     |
| ------------ | ----- | ----- | ------- | --- | --------- | ----- | --- | --- | --- | --- | --- | --- |
pages261–265.IEEE,2016.
| Yong | Wu, | Mu Li, | Vin Sharma, | Zachary | Tatlock, | and |     |     |     |     |     |     |
| ---- | --- | ------ | ----------- | ------- | -------- | --- | --- | --- | --- | --- | --- | --- |
Yida Wang. Nimble: Efficiently compiling dynamic [55] LeyuanWang,ZhiChen,YizhiLiu,YaoWang,Lianmin
| neural | networks |     | for model | inference. | arXiv | preprint |                         |     |     |     |                      |     |
| ------ | -------- | --- | --------- | ---------- | ----- | -------- | ----------------------- | --- | --- | --- | -------------------- | --- |
|        |          |     |           |            |       |          | Zheng,MuLi,andYidaWang. |     |     |     | Aunifiedoptimization |     |
arXiv:2006.03031,2020. approachforcnn modelinference on integratedgpus.
InProceedingsofthe48thInternationalConferenceon
| [46] Patricia | Suriana, |     | Andrew Adams, |     | and Shoaib | Kamil. |     |     |     |     |     |     |
| ------------- | -------- | --- | ------------- | --- | ---------- | ------ | --- | --- | --- | --- | --- | --- |
ParallelProcessing,pages1–10,2019.
| Parallel | associative |     | reductions | in  | halide. | In 2017 |     |     |     |     |     |     |
| -------- | ----------- | --- | ---------- | --- | ------- | ------- | --- | --- | --- | --- | --- | --- |
IEEE/ACMInternationalSymposiumonCodeGener- [56] RClintonWhaleyandJackJDongarra. Automatically
ationandOptimization(CGO),pages281–291.IEEE, tunedlinearalgebrasoftware. InSC’98:Proceedings
2017.
ofthe1998ACM/IEEEconferenceonSupercomputing,
pages38–38.IEEE,1998.
| [47] RichardSSuttonandAndrewGBarto. |     |     |     |     | Reinforcement |     |     |     |     |     |     |     |
| ----------------------------------- | --- | --- | --- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- |
learning:anintroduction. MITpress,2018. [57] Fisher Yu and Vladlen Koltun. Multi-scale context
|                                         |     |     |     |     |         |     | aggregation | by  | dilated | convolutions. |     | arXiv preprint |
| --------------------------------------- | --- | --- | --- | --- | ------- | --- | ----------- | --- | ------- | ------------- | --- | -------------- |
| [48] PhilippeTillet,HTKung,andDavidCox. |     |     |     |     | Triton: | an  |             |     |         |               |     |                |
arXiv:1511.07122,2015.
intermediatelanguageandcompilerfortiledneuralnet-
| work | computations. |     | In Proceedings |     | of the | 3rd ACM |     |     |     |     |     |     |
| ---- | ------------- | --- | -------------- | --- | ------ | ------- | --- | --- | --- | --- | --- | --- |
[58] LianminZheng,ChengfanJia,MinminSun,ZhaoWu,
SIGPLANInternationalWorkshoponMachineLearn- CodyHaoYu,AmeerHaj-Ali,YidaWang,JunYang,
ingandProgrammingLanguages,pages10–19,2019.
|              |            |     |           |          |           |     | DanyangZhuo,KoushikSen,etal. |     |        |          | Ansor:generating |                |
| ------------ | ---------- | --- | --------- | -------- | --------- | --- | ---------------------------- | --- | ------ | -------- | ---------------- | -------------- |
|              |            |     |           |          |           |     | high-performance             |     | tensor | programs | for              | deep learning. |
| [49] Nicolas | Vasilache, |     | Oleksandr | Zinenko, | Theodoros |     |                              |     |        |          |                  |                |
https://arxiv.org/abs/2006.06762,2020.
Theodoridis,PriyaGoyal,ZacharyDeVito,WilliamS
Moses,SvenVerdoolaege,AndrewAdams,andAlbert
[59] SizeZheng,YunLiang,ShuoWang,RenzeChen,and
| Cohen. | Tensorcomprehensions: |     |     | framework-agnostic |     |     |              |     |                                   |     |     |     |
| ------ | --------------------- | --- | --- | ------------------ | --- | --- | ------------ | --- | --------------------------------- | --- | --- | --- |
|        |                       |     |     |                    |     |     | KaiwenSheng. |     | Flextensor:anautomaticscheduleex- |     |     |     |
high-performancemachinelearningabstractions. arXiv plorationandoptimizationframeworkfortensorcompu-
preprintarXiv:1802.04730,2018.
|     |     |     |     |     |     |     | tationonheterogeneoussystem. |     |     |     | InProceedingsofthe |     |
| --- | --- | --- | --- | --- | --- | --- | ---------------------------- | --- | --- | --- | ------------------ | --- |
Twenty-FifthInternationalConferenceonArchitectural
| [50] Nicolas | Vasilache, |     | Oleksandr | Zinenko, | Theodoros |     |         |                 |     |           |     |               |
| ------------ | ---------- | --- | --------- | -------- | --------- | --- | ------- | --------------- | --- | --------- | --- | ------------- |
|              |            |     |           |          |           |     | Support | for Programming |     | Languages |     | and Operating |
Theodoridis,PriyaGoyal,ZacharyDevito,WilliamS
Systems,pages859–873,2020.
Moses,SvenVerdoolaege,AndrewAdams,andAlbert
| Cohen. | Thenext700acceleratedlayers:frommathe- |     |     |     |     |     |     |     |     |     |     |     |
| ------ | -------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
[60] ZhenZheng,PengzhanZhao,GuopingLong,Feiwen
maticalexpressionsofnetworkcomputationgraphsto Zhu,KaiZhu,WenyiZhao,LansongDiao,JunYang,
| acceleratedgpukernels,automatically. |     |     |     |     | ACMTransac- |     |            |                                      |     |     |     |     |
| ------------------------------------ | --- | --- | --- | --- | ----------- | --- | ---------- | ------------------------------------ | --- | --- | --- | --- |
|                                      |     |     |     |     |             |     | andWeiLin. | Fusionstitching:boostingmemoryinten- |     |     |     |     |
tionsonArchitectureandCodeOptimization(TACO),
|                  |     |     |     |     |     |     | sivecomputationsfordeeplearningworkloads. |     |     |     |     | arXiv |
| ---------------- | --- | --- | --- | --- | --- | --- | ----------------------------------------- | --- | --- | --- | --- | ----- |
| 16(4):1–26,2019. |     |     |     |     |     |     | preprintarXiv:2009.10924,2020.            |     |     |     |     |       |
USENIX Association 14th USENIX Symposium on Operating Systems Design and Implementation    879
