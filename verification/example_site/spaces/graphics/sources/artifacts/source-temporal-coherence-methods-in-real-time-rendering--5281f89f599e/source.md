# Temporal Coherence Methods in Real-Time Rendering

DOI:10.1111/j.1467-8659.2012.03075.x COMPUTERGRAPHICS forum
Volume31(2012),number8 pp.2378–2408
Temporal Coherence Methods in Real-Time Rendering
DanielScherzer1,LeiYang2,OliverMattausch3,4,DiegoNehab5,PedroV.Sander2,MichaelWimmer3andElmarEisemann6
1MPIInformatik,2HongKongUST,3TUVienna,4UZurich,5IMPA,and6DelftUniversityofTechnology/TelecomParisTech
scherzer@mpi-inf.mpg.de,yanglei@alumni.ust.hk,psander@cse.ust.hk,{matt,wimmer}@cg.tuwien.ac.at,diego@impa.br,
elmar.eisemann@telecom-paristech.fr
Abstract
Nowadays,thereisastrongtrendtowardsrenderingtohigher-resolutiondisplaysandathighframerates.This
developmentaimsatdeliveringmoredetailandbetteraccuracy,butitalsocomesatasignificantcost.Although
graphicscardscontinuetoevolvewithanever-increasingamountofcomputationalpower,thespeedgainiseasily
counteracted by increasingly complex and sophisticated shading computations. For real-time applications, the
directconsequenceisthatimageresolutionandtemporalresolutionareoftenthefirstcandidatestobowtothe
performanceconstraints(e.g.althoughfullHDispossible,PS3andXBoxoftenrenderatlowerresolutions).
Inordertoachievehigh-qualityrenderingatalowercost,onecanexploittemporalcoherence(TC).Theunderlying
observationisthatahigherresolutionandframeratedonotnecessarilyimplyamuchhigherworkload,buta
largeramountofredundancyandahigherpotentialforamortizingrenderingoverseveralframes.Inthissurvey,we
investigatemethodsthatmakeuseofthisprincipleandprovidepracticalandtheoreticaladviceonhowtoexploit
TC for performance optimization. These methods not only allow incorporating more computationally intensive
shadingeffectsintomanyexistingapplications,butalsoofferexcitingopportunitiesforextendinghigh-endgraphics
applicationstolower-specconsumer-levelhardware.Tothisend,wefirstintroducethenotionandmainconceptsof
TC,includinganoverviewofhistoricalmethods.Wethendescribeageneralapproach,image-spacereprojection,
with several implementation algorithms that facilitate reusing shading information across adjacent frames. We
alsodiscussdata-reusequalityandperformancerelatedtoreprojectiontechniques.Finally,inthesecondhalfof
thissurvey,wedemonstratevariousapplicationsthatexploitTCinreal-timerendering.
Keywords: anti-aliasing, frameinterpolation, globalillumination, image-basedrendering, largedatavisual-
ization, level-of-detail, non-photo-realisticrendering, occlusionculling, perception-basedrendering, remote
rendering, sampling, shadows, streaming, temporalcoherence, upsampling
ACMCCS: I.3.3[ComputerGraphics]:Picture/ImageGeneration—DisplayAlgorithms; ViewingAlgorithms;
I.3.7[ComputerGraphics]:Three-DimensionalGraphicsandRealism—Color,shading,shadowingandtexture
1. Introduction inthepastdecade,thegeneralsenseisthatatleastinthefore-
seeablefuture,anyhardwareimprovementwillbereadilyput
In order to satisfy the ever-increasing market demand for
tousetowardsoneofthesegoals.
richergamingexperiences,developersofreal-timerendering
applicationsareconstantlylookingforcreativewaystofitin- The immense computational power required to render a
creasedphoto-realism,frameratesandresolutionwithinthe singleframewithdesirableeffectssuchasphysicallycorrect
computationalbudgetofferedbyeachnewgraphicshardware shadows,depth-of-field,motion-blurandglobalillumination
generation.Althoughgraphicshardwareevolvedremarkably (or even an effective ambient-occlusion approximation) is
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographics
AssociationandBlackwellPublishingLtd.Publishedby
BlackwellPublishing,9600GarsingtonRoad,OxfordOX4
2DQ,UKand350MainStreet,Malden,MA02148,USA.
2378

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2379
Figure1: Real-timerenderingapplicationsexhibitaconsiderableamountofspatio-temporalcoherence.Thisistrueforcamera
motion,asintheParthenonsequence(left),aswellasanimatedscenessuchastheHeroine(middle)andNinja(right)sequences.
Diagramstotherightofeachrenderingshowdisoccludedpointsinred,incontrasttopointsthatwerevisibleintheprevious
frame,whichareshowningreen(i.e.greenpointsareavailableforreuse).[ImagescourtesyofAdvancedMicroDevices,Inc.,
Sunnyvale,California,USA]
multipliedbythedemandsofhigh-resolutiondisplays,which
requirelargescenedescriptionstobemanipulated(geometry
| and textures). | The | difficulty | is compounded | further | by the |     |     |     |     |     |
| -------------- | --- | ---------- | ------------- | ------- | ------ | --- | --- | --- | --- | --- |
needtogeneratesuchframescontinuously,aspartofreal-
timeanimation.
| Although        | rendering | at 30       | Hz (NTSC) | is already           | consid- |     |     |     |     |     |
| --------------- | --------- | ----------- | --------- | -------------------- | ------- | --- | --- | --- | --- | --- |
| ered real-time, | most      | modern      | liquid    | crystal display      | (LCD)   |     |     |     |     |     |
| monitors        | and TVs   | can refresh | at least  | at 60 Hz. Naturally, |         |     |     |     |     |     |
developersstrivetomeetthisstandard.Giventhatthereisstill
| a measurable | task-performance |     | improvement | in interactive |     |     |     |     |     |     |
| ------------ | ---------------- | --- | ----------- | -------------- | --- | --- | --- | --- | --- | --- |
applicationsasframeratesincreaseupto120Hz[DER*10b],
thereisjustificationtotargetsuchhighframerates.Inthis
case,aslittleas8msareavailabletoproduceeachcomplete
photo-realisticimage,andallinvolvedcalculations(includ-
|     |     |     |     |     |     | Figure2: | Plotshowsthepercentageofsurfacepointsthat |     |     |     |
| --- | --- | --- | --- | --- | --- | -------- | ----------------------------------------- | --- | --- | --- |
ingphysicalsimulationsandothertasksunrelatedtorender-
remainvisiblefromoneframetothenextfortheanimations
ingitself)havetofitwithinthistimebudget.Needlesstosay,
ofFigure1Coherenceinexcessof90%istypicalofmany
thisposesadifficulttask.
game-likescenes.
Thetraditionalapproachtooptimizationinthecontextof
|     |     |     |     |     |     | reduction | in the average | cost of rendering | a frame | can be |
| --- | --- | --- | --- | --- | --- | --------- | -------------- | ----------------- | ------- | ------ |
real-timerenderingistofocusonimprovingtheperformance
usedinavarietyofways:fromsimplyincreasingtheframe
ofindividualrenderingtasks,oneatatime.Inthissurvey,we
presentresultsthatareconnectedbyamoregeneralapproach ratetoimprovingthequalityofeachrenderedframe.
tooptimization:exploitingtemporalcoherence(TC). Naturally,TChasbeenexploitedsincetheearlydaysof
|          |              |       |     |                |       | computer | graphics. We | describe a variety | of early | applica- |
| -------- | ------------ | ----- | --- | -------------- | ----- | -------- | ------------ | ------------------ | -------- | -------- |
| Consider | the examples | shown | in  | Figure 1. When | frame |          |              |                    |          |          |
ratesarehigh,thereareonlyverysmallchangesfromone tions in Section 2. In Section 3, we move to methods that
canbeusedtotakeadvantageofTCinreal-timerendering
frametothenext.Eachvisiblesurfacepointtendstoremain
scenarios.Specialattentionisgiventotechniquesbasedon
| visible across | the | interval | of several | frames. Furthermore, |     |     |     |     |     |     |
| -------------- | --- | -------- | ---------- | -------------------- | --- | --- | --- | --- | --- | --- |
reprojection.Reprojectionallowsustomapasurfacepoint
pointattributes(includingcolour)tendtomaintaintheirval-
inoneframetothesamesurfacepointinapreviouslyren-
uesalmostunchangedthroughout.Tomeasuretheamountof
|     |     |     |     |     |     | dered frame. | This mapping | plays a key | role in | the reuse |
| --- | --- | --- | --- | --- | --- | ------------ | ------------ | ----------- | ------- | --------- |
TCintheseanimationsequences,Figure2plotsthefraction
ofinformationacrossframes.Reusinginformationinvolves
ofpointsthatremainvisiblefromoneframetothenext.We
|     |     |     |     |     |     | certain quality/performance |     | trade-offs | that are | analyzed in |
| --- | --- | --- | --- | --- | --- | --------------------------- | --- | ---------- | -------- | ----------- |
canseethatfractionsof90%andhigheraretypical.
|     |     |     |     |     |     | Section 4. | Since the selection | of a proper | target | for reuse |
| --- | --- | --- | --- | --- | --- | ---------- | ------------------- | ----------- | ------ | --------- |
Sinceanever-increasingsliceoftherenderingbudgetis canmodulatethistrade-off,thesamesectiondiscussesthe
mostimportantfactorsinfluencingthischoice.InSection5,
| dedicated | to shading | surface | points, | such a high level | of  |     |     |     |     |     |
| --------- | ---------- | ------- | ------- | ----------------- | --- | --- | --- | --- | --- | --- |
TC presents a great opportunity for optimization. Rather wethencategorizeanddiscussanumberofapplicationsthat
than wastefully recomputing every frame in its entirety takeadvantageofTCinreal-timerendering,includingboth
from scratch, we can reuse information computed during theonesthatusereprojection,andtheonesthatexploitTC
thecourseofoneframe(intermediateresults,orevenfinal inotherspaces.Finally,inSection6,weprovideasummary
colours)tohelprenderthefollowingframes.Theresulting ofthepresentation.
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2380 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
2. EarlyApproaches sceneintodifferentlayers[RP94,LS97],whileothersaug-
menttheimage-basedrepresentationwithdepthinformation
TChasbeenaroundforalmostaslongascomputergraphics
[SGHS98].Inthisreport,however,wewillfocusonmeth-
itself.Forexample,thetermframe-to-framecoherencewas
odsthatdonotuseproxygeometrytocacheinformation,but
firstintroducedbySutherlandetal.[SSS74]inhisseminal
directlyreuserenderedinformationfromthepreviousframe
paper‘CharacterizationofTenHidden-SurfaceAlgorithms’.
buffers.
Therefore,wewillsummarizeearlydevelopmentsinwhich
TCwasalreadyusedinsimilarways.
Inparticular,wewillcovertheuseofTCinray-tracing, 2.3. Imageandrendercaches
image-basedrendering,andimageandrendercaches.
Imageandrendercachesstoretheinformationgeneratedin
previousframesinadatastructure,andreusethisinforma-
2.1. Ray-tracing
tionforthegenerationofthecurrentframe,usingdifferent
|     |     |     |     |     |     |     | reconstruction | and mostly | forward | reprojection | techniques |
| --- | --- | --- | --- | --- | --- | --- | -------------- | ---------- | ------- | ------------ | ---------- |
TCwasalreadyusedfortheclassicalray-tracingalgorithm
(Section3.2).
inordertospeedupthecalculationofanimationsequences.
| While these | techniques | are | for offline | rendering, | most | of  |     |     |     |     |     |
| ----------- | ---------- | --- | ----------- | ---------- | ---- | --- | --- | --- | --- | --- | --- |
Wimmeretal.[WGS99]proposedatechniquethataccel-
themalreadymakeuseofforwardreprojection(Section3.2) erates the rendering of complex environments by splitting
forreusinginformation. thesceneintoanearfieldandafarfield:Thenearfieldis
Badt[BJ88]developed aforwardreprojectionalgorithm renderedusingthetraditionalrenderingpipeline,whileray
that uses object space information stored from the previ- castingisusedforthefarfield.Tominimizethenumberof
|     |     |     |     |     |     |     | rays cast, | they use a panoramic | image | cache | and only re- |
| --- | --- | --- | --- | --- | --- | --- | ---------- | -------------------- | ----- | ----- | ------------ |
ousframe.Thisallowsapproximatingray-tracedanimation
|           |                   |     |         |     |               |     | compute | rays if a cache | entry is not | valid anymore, | where |
| --------- | ----------------- | --- | ------- | --- | ------------- | --- | ------- | --------------- | ------------ | -------------- | ----- |
| frames of | diffuse polygons. |     | Adelson | and | Hodges [AH95] |     |         |                 |              |                |       |
validityisbasedonthedistancetotheoriginalobserverpo-
laterextendedtheapproachtoray-tracingofarbitraryscenes.
sitionwherethepixelwasgenerated.Thepanoramicimage
Havranetal.[HBS03]reusedray/objectintersectionsinray-
castedwalkthroughs.Theydothisbyreprojectingandsplat- cache avoids reprojection altogether, but quickly becomes
inaccuratefortranslationalmotion.
tingvisiblepointsamplesfromthelastframeintothecurrent,
therebyavoidingthecostlyraytraversalformorethan78% Qu et al. [QWQK00] proposed using image warping to
ofthepixelsintheirtestscenes.
accelerateray-casting.Theideaistowarptheoutputimage
ofthepreviousframeintothecurrentframeusingforward
| Leaving | the concept | of  | frame-based | rendering |     | behind, |     |     |     |     |     |
| ------- | ----------- | --- | ----------- | --------- | --- | ------- | --- | --- | --- | --- | --- |
projection.Duetothewarping,pixelsmayfallbetweenthe
| Bishop et | al. [BFMZ94] | introduced |     | frameless | rendering, |     |     |     |     |     |     |
| --------- | ------------ | ---------- | --- | --------- | ---------- | --- | --- | --- | --- | --- | --- |
gridpositionsofthepixelsofthecurrentframe;therefore,
whichheavilyreliesuponTCforsensibleoutput.Here,each
anoffsetbufferisusedtostoretheexactpositions.Dueto
pixelisrenderedindependentlybasedonthemostrecentin-
put, thereby minimizing lag. There is no wait period until disocclusions, holes can occur at some pixels. Here, ray-
castingisusedtogeneratethesemissingpixels.Theauthors
| all pixels | of a frame | are drawn, | but | individual | pixels | stay |          |               |             |             |          |
| ---------- | ---------- | ---------- | --- | ---------- | ------ | ---- | -------- | ------------- | ----------- | ----------- | -------- |
|            |            |            |     |            |        |      | proposed | to use an age | stored with | each pixel, | which is |
visibleforarandomtimespan,untiltheyarereplacedwith
|            |             |      |               |     |          |         | increased | with each warping | step | to account | for the lower |
| ---------- | ----------- | ---- | ------------- | --- | -------- | ------- | --------- | ----------------- | ---- | ---------- | ------------- |
| an updated | pixel. Note | that | this approach |     | does not | use the |           |                   |      |            |               |
qualityofpixelsthathavebeenwarped(repeatedly).Upon
| object coherence | that | is an | integral | part of | many polygon |     |     |     |     |     |     |
| ---------------- | ---- | ----- | -------- | ------- | ------------ | --- | --- | --- | --- | --- | --- |
renderers. To avoid image tearing, pixels are rendered in a renderinganewoutputframe,thisagecanbeusedtodecide
ifapixelshouldbere-renderedorreused.
randomorder.Dayaletal.[DWWL05]combinedthiswith
temporalreprojectionandadaptivereconstruction,focusing Walteretal.[WDP99]introducedtherendercache.Itis
onedgesanddynamicpartsofthescene.
intendedasanaccelerationdatastructureforrenderersthat
aretooslowforinteractiveuse.Incontrasttothepreviously
2.2. Image-basedrendering mentionedapproaches,whichstorepixelcolours,therender
cacheisapoint-basedstructure,whichstoresthecomplete
Inageneralsense,TCisalsorelatedtomethodsthatreplace
3Dcoordinatesofrenderedpointsandshadinginformation.
parts of a scene with image-based proxy representations. By using reverse reprojection, these results can be reused
| This can | be interpreted | as  | a form | of reverse | reprojection |     |                |                    |     |            |               |
| -------- | -------------- | --- | ------ | ---------- | ------------ | --- | -------------- | ------------------ | --- | ---------- | ------------- |
|          |                |     |        |            |              |     | in the current | frame. Progressive |     | refinement | allows decou- |
(Section3.1)appliedtoindividualpartsofascene.Thisidea
|     |     |     |     |     |     |     | pling the | rendering and | display frame | rates, | enabling high |
| --- | --- | --- | --- | --- | --- | --- | --------- | ------------- | ------------- | ------ | ------------- |
wasusedmostprominentlyintheso-calledhierarchicalim-
interactivity.Walteretal.[WDG02]extendedthisapproach
agecacheanditsvariations[Sch96,SLS*96],whereimages
withpredictivesamplingandinterpolationfilters,whilelater
(calledimpostors)ofcomplexdistantgeometryaregenerated workacceleratedtherendercacheontheGPU[VALBW06,
| on the fly | and reused | in subsequent |     | frames, | thus reducing |     |     |     |     |     |     |
| ---------- | ---------- | ------------- | --- | ------- | ------------- | --- | --- | --- | --- | --- | --- |
ZWL05].
| rendering | times. The | geometric | error | for | such systems | has |     |     |     |     |     |
| --------- | ---------- | --------- | ----- | --- | ------------ | --- | --- | --- | --- | --- | --- |
alsobeenformallyanalyzed[ED07a].Frame-to-framecoher- WardandSimmons[WS99]describedtheHolodeckray
enceisfurtherexploitedinvarioussystemsthatpartitionthe cache,whichconvertsrenderedsamplesintoaspherical4D
|     |     |     |     |     |     |     |     |     |     | (cid:2)c 2012TheAuthors |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------------------- | --- |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2381
| mesh centred | at the viewpoint. | The mesh | can then be dis- |     |     |     |     |     |     |
| ------------ | ----------------- | -------- | ---------------- | --- | --- | --- | --- | --- | --- |
playedfordifferentviewpoints.Basedonthismethod,Sim-
monsandSe´quin[SS00]proposedtheTapestryrepresenta-
tionbyintroducingincrementalre-centringofthespherical
mesh,aswellasotherenhancementssuchasprioritizedsam-
plingandautomaticsampleinvalidation.
3. ReprojectionandDataReuse
AnimportantdecisionwhenutilizingTCishowtheprevi- Figure3: Thereversereprojectionoperator.Theshadingre-
sultandpixeldepthsoftimet−1arestoredinscreen-space
ouslycomputeddataarestored,tracked,retrievedandreused.
Onmoderngraphicshardware,themostcommonwayisto framebuffers (left). For each pixel p at time t (right), its
storethedesireddataatvisiblesurfacepointsinviewport- reprojectedpositionπ (p)iscomputedtolocatethecor-
t−1
|     |     |     |     | responding | position | at frame | t−1. The | recomputed | scene |
| --- | --- | --- | --- | ---------- | -------- | -------- | -------- | ---------- | ----- |
sizedoff-screenbuffersateachrenderedframe,usuallyre-
ferred to as history buffer, payload buffer or cache. When depthiscomparedtothestoredpixeldepth.Apairofmatch-
generatingthefollowingframes,thedatainthebufferarere- ing depths indicate a cache hit (p ), whereas inconsistent
2
projectedtotheirnewlocationsbasedonscenemotion.Even depthsindicateacachemiss(p ).
1
withhardwaresupport,reprojectioncanstillbeacomputa-
| tionally challenging                              | task. In   | this section,     | we first describe |                          |     |     |                                       |     |     |
| ------------------------------------------------- | ---------- | ----------------- | ----------------- | ------------------------ | --- | --- | ------------------------------------- | --- | --- |
| two reprojection                                  | strategies | that are commonly | used in nu-       |                          |     |     |                                       |     |     |
|                                                   |            |                   |                   | pandthereprojectedpixelf |     |     | (x(cid:4),y(cid:4))areindeedgenerated |     |     |
| merousapplicationsandcansometimesbeinterchangedto |            |                   |                   |                          |     | t−1 |                                       |     |     |
suitspecialneeds.Indisoccludedregionswheretheprevious by the same surface point. In this case, the previous value
data are not available, we show how to fill in approximate canbereused.Otherwisenocorrespondenceexistsandwe
resultsthatarevisuallyplausible.Finally,wedescribeamor- denote this by π t−1 (p)=∅, which we refer to as a cache
miss.Additionaltestssuchasobject-IDequalitycanalsobe
tizedsampling,whichisabasisusedinvariousapplications
employedtoreinforcethiscachemissdecision.Thereverse
describedinSection5.
reprojectionoperationisillustratedinFigure3.
3.1. Reversereprojection
3.1.1. Implementation
| A basic | scenario of using | TC is to | generate a new frame |         |           |        |              |        |        |
| ------- | ----------------- | -------- | -------------------- | ------- | --------- | ------ | ------------ | ------ | ------ |
|         |                   |          |                      | The RRC | algorithm | can be | conveniently | mapped | to the |
usingdatafromapreviouslyshadedframe.Foreachpixelin
|     |     |     |     | modern programmable |     | rendering | pipeline. | A   | major task |
| --- | --- | --- | --- | ------------------- | --- | --------- | --------- | --- | ---------- |
thenewframe,wecantracebacktoitspositionintheear-
|                                                     |     |     |     | of this is | to compute | the        | reprojection      | operator | π (p),     |
| --------------------------------------------------- | --- | --- | --- | ---------- | ---------- | ---------- | ----------------- | -------- | ---------- |
| liercachedframetodetermineifitwaspreviouslyvisible. |     |     |     |            |            |            |                   |          | t−1        |
|                                                     |     |     |     | which maps | each       | pixel p to | its corresponding |          | clip-space |
Ifavailable,thiscachedvaluecanbereusedinplaceofper-
|     |     |     |     |     |     |     | t−1. |     | t,  |
| --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- |
forminganexpensivecomputation.Otherwiseitmustbere- position in the previous frame At frame the ho-
|     |     |     |     |           |            |       |             | (x ,y | ,z ,w      |
| --- | --- | --- | --- | --------- | ---------- | ----- | ----------- | ----- | ---------- |
|     |     |     |     | mogeneous | projection | space | coordinates | t     | t t t)vert |
computedfromscratch.ThistechniqueiscalledtheReverse
|     |     |     |     | of each | vertex v | are calculated | in the | vertex | shader, to |
| --- | --- | --- | --- | ------- | -------- | -------------- | ------ | ------ | ---------- |
ReprojectionCache(RRC).Itwasproposedindependently
|     |     |     |     | which the | application | has provided | the | world, | view and |
| --- | --- | --- | --- | --------- | ----------- | ------------ | --- | ------ | -------- |
byNehabetal.[NSL*07]andScherzeretal.[SJW07],and
|     |     |     |     | projection | matrices | and any | animation | parameters. | To per- |
| --- | --- | --- | --- | ---------- | -------- | ------- | --------- | ----------- | ------- |
servesasaframeworkforanumberofapplicationsdescribed
inSection5. form correct reprojection, the application also has to pro-
t−1
|     |     |     |     | vide these | matrices | and animation | parameters |     | at  |
| --- | --- | --- | --- | ---------- | -------- | ------------- | ---------- | --- | --- |
Formally,letf tdenotethecachegeneratedattimet,which to the vertex shading stage. In addition to transforming
isaframebufferholdingthepixeldatavisibleatthatframe. the vertex at frame t, the vertex shader also transforms
Inadditiontof t,wekeepanaccompanyingbufferd which the vertex using the matrices and parameters from frame
t
holds the scene depth in screen space. Let f t(p) and d t(p) t−1, thereby computing the projection-space coordinates
|     |     | p∈Z2. |     | (x ,y | ,z ,w | ofthesamevertexatframet−1. |     |     |     |
| --- | --- | ----- | --- | ----- | ----- | -------------------------- | --- | --- | --- |
denote the buffer values at pixel For each pixel t−1 t−1 t−1 t−1 )vert
| p=(x,y) | t,  |     |     |     |     |     |     |     |     |
| ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
at time we determine the 3D clip-space posi- Thesecoordinatesarestoredasvertexattributesandareau-
tionofitsgeneratingscenepointatframet−1,denotedby tomaticallyinterpolatedbythehardwarebeforereachingthe
(x(cid:4),y(cid:4),z(cid:4))=π (p).Here,thereprojectionoperatorπ (p) pixel stage. This gives each pixel p access to the previous
|     | t−1 |     | t−1 |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
mapsapointptoitspreviouspositionatframet−1.Note projection-spacecoordinates(x ,y ,z ,w )pix.The
|     |     |     |     |     |     |     | t−1 t−1 | t−1 | t−1 |
| --- | --- | --- | --- | --- | --- | --- | ------- | --- | --- |
finalcachecoordinateπ
thatwiththisreprojectionoperation,wealsoobtainthedepth t−1 (p)isobtainedwithasimpledi-
|     |     | z(cid:4) | t−1. |     | (w  |     |     |     |     |
| --- | --- | -------- | ---- | --- | --- | --- | --- | --- | --- |
of the generating scene point at frame This depth vision by t−1 )pix within the pixel shader. Note that the
is used to test whether the current point was visible in the transformation need only be computed at the vertex level,
previousframe.Ifthereprojecteddepthz(cid:4)equalsd (x(cid:4),y(cid:4)) therebysignificantlyreducingthecomputationaloverheadin
t−1
| (withinagiventolerance),weconcludethatthecurrentpixel |     |     |     | mostscenes. |     |     |     |     |     |
| ----------------------------------------------------- | --- | --- | --- | ----------- | --- | --- | --- | --- | --- |
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2382 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
Becauseofarbitraryscenemotionandanimation,thepre- ality on the GPU (available through CUDA or DirectX 11
viouspositionπ (p)usuallyliessomewherebetweenthe Compute Shader). For each pixel in the cache, they deter-
t−1
setofdiscretesamplesinthecachef
t−1 ,andthussomeform mine its new position in the target frame by offsetting its
ofresamplingisrequired.Nehabetal.[NSL*07]suggested currentpositionusingtheforwardmotionvector(disparity
usinghardware-assistedbilineartexturefetchforresampling. vector).Then,thedepthofthecurrentpixelistestedagainst
Inmostsituations,thissufficesforpracticaluse.Itisalsoused thetargetpixelforresolvingvisibility.Thisoperationisper-
toreconstructthepreviousdepthvaluesothatamorerobust formedusingtheatomicminfunctionalitytoavoidparallel
cache-missdetectioncanbeachieved. writeconflicts.Notethatsincethereisnoone-to-onemap-
pingbetweenthesourceandthetargetpixels,holescanbe
presentafterreprojection.Toresolvethis,Yuetal.[YWY10]
3.2. Forwardreprojection proposedtoincreasethesupportsizeofthereprojectedpixel,
i.e.towritetoallfourneighboursofeachreprojectedfrac-
Alternatively,insteadofstartingfromeverypixelinthetar-
getframe,wecandirectlyprocessthecacheandmapevery tionalposition.Thisworkswithnear-viewwarpingfortheir
applicationoflight-fieldgeneration,butmaybeinsufficient
| pixel in the | cache | to its | new position. | This | has the | advan- |     |     |     |     |     |     |
| ------------ | ----- | ------ | ------------- | ---- | ------- | ------ | --- | --- | --- | --- | --- | --- |
forotherapplicationswherenon-uniformmotionisinvolved.
tagethatitdoesnotrequireprocessingthescenegeometry
forthenewframe,whichisdesirableinsomeapplications.
Recently,Yangetal.[YTS*11]proposedanimage-based
Still,itrequiresaforwardmotionvector(ordisparityvector)
approachforforwardreprojectionusingconventionalGPU
generatedforeachpixel,whichisequivalenttotheinverse
|            |      |     |     |     |     |     | pixel-shading | functionality, | i.e. | pixel gathering | as  | opposed |
| ---------- | ---- | --- | --- | --- | --- | --- | ------------- | -------------- | ---- | --------------- | --- | ------- |
| mappingofπ | (p). |     |     |     |     |     |               |                |      |                 |     |         |
t−1 to scattering. The essence of the approach is an iterative
|     |     |     |     |     |     |     | image-space | search | performed | independently | at  | each pixel |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ------ | --------- | ------------- | --- | ---------- |
Ontheotherhand,per-pixelforwardprojectioncanbedif-
|     |     |     |     |     |     |     | in the target | frame, | in order | to find the motion | vector | that |
| --- | --- | --- | --- | --- | --- | --- | ------------- | ------ | -------- | ------------------ | ------ | ---- |
ficultandcostlytoimplementonconventionalgraphicshard-
ware (prior to DirectX 11) because it involves a scattering leads to the corresponding pixels in the rendered frames.
|     |     |     |     |     |     |     | This approach | effectively | inverts | the reprojection |     | operator |
| --- | --- | --- | --- | --- | --- | --- | ------------- | ----------- | ------- | ---------------- | --- | -------- |
operation,whichdoesnotmapwelltothetraditionalgraphics
|     |     |     |     |     |     |     | π (p) based | on  | the assumption | that π | (p) is | piecewise |
| --- | --- | --- | --- | --- | --- | --- | ----------- | --- | -------------- | ------ | ------ | --------- |
pipeline. For example, splatting each pixel from the previ- t−1 t−1
smoothovertheimage.Discontinuityishandledbyseveral
ousframetoitsreprojectedpositioninthecurrentframecan
additionalsearchinitializationheuristics.Theentireprocess
beslowandleaveholes.Itmayalsorequireapplyingcom-
plexfilteringstrategiesinordertoobtainpixel-accuratere- fitsinapixelshaderandproducesconvincingresultswithin
asmalltimebudget.
sults.AwayaroundtheseproblemswasdescribedbyDidyk
| et al. [DER*10b]: |     | they | proposed | an image-warping |     | tech- |     |     |     |     |     |     |
| ----------------- | --- | ---- | -------- | ---------------- | --- | ----- | --- | --- | --- | --- | --- | --- |
nique,whichisefficientonconventionalGPUs.Thewarping
isachievedbyapproximatingthemotionvectorfieldwitha 3.3. Handlingdisocclusion
coarsegridrepresentation,assumingthatthevectorfieldis
Theprocessofreprojectionisessentiallyanon-linearwarp-
piecewiselinear.Aninitialuniformgridissnappedtolarge
ingandmayleavethenewlydisoccludedregionsincorrectly
| motion vector | discontinuities |     | in the | previous | frame. | Then, |     |     |     |     |     |     |
| ------------- | --------------- | --- | ------ | -------- | ------ | ----- | --- | --- | --- | --- | --- | --- |
shadedorblank.Withreversereprojection,wemayhavethe
| the grid geometry |     | is rendered | to  | its new | position | dictated |     |     |     |     |     |     |
| ----------------- | --- | ----------- | --- | ------- | -------- | -------- | --- | --- | --- | --- | --- | --- |
optiontoreshadetheseregionswheneveracachemissoc-
| by the motion | vector | field | so that | its associated |     | texture is |     |     |     |     |     |     |
| ------------- | ------ | ----- | ------- | -------------- | --- | ---------- | --- | --- | --- | --- | --- | --- |
automatically warped. Occlusion and disocclusion are nat- curs.However,thisisnotalwaysdesirableduetolimitedtime
budgetorotherconstraintsimposedbytheapplication.With
| urally handled | with | grid       | folding  | and stretching. |           | Note that |                       |     |          |            |             |       |
| -------------- | ---- | ---------- | -------- | --------------- | --------- | --------- | --------------------- | --- | -------- | ---------- | ----------- | ----- |
|                |      |            |          |                 |           |           | forward reprojection, |     | there is | usually no | such option | since |
| depth testing  | must | be enabled | in order | to              | correctly | resolve   |                       |     |          |            |             |       |
theshadinginputmaynotbeavailable.Therefore,someform
occlusionsandfold-overs.
ofapproximateholefillingneedstobeperformedinorderto
AregulargridusedbyDidyketal.[DER*10b]canhave
reducevisualartefacts.
| difficulties | warping | images | with | finely detailed |     | geometry. |     |     |     |     |     |     |
| ------------ | ------- | ------ | ---- | --------------- | --- | --------- | --- | --- | --- | --- | --- | --- |
Andreev[And10]suggestedaninpaintingstrategythatdu-
| They later | proposed | an improved |     | algorithm | using | adaptive |     |     |     |     |     |     |
| ---------- | -------- | ----------- | --- | --------- | ----- | -------- | --- | --- | --- | --- | --- | --- |
plicatesandoffsetsneighbouringimagepatchesintothehole
grids[DRE*10].Theirnewapproachstartswitharegulargrid
areafromthefoursides.Thisisefficientlyimplementedina
(32×32).Thenageometryshadertraversesallthequadsin
thegridinparallel.Everyquadthatcontainsadiscontinuity pixelshaderandcanbeperformediterativelyuntilthehole
iscompletelyfilled.Foramorerobustsolution,onecancon-
| is further | partitioned | in  | four. This | process | is iterated | until |     |     |     |     |     |     |
| ---------- | ----------- | --- | ---------- | ------- | ----------- | ----- | --- | --- | --- | --- | --- | --- |
siderusingpull–pushinterpolation[MKC07].Thepull–push
| no quads      | need to | be further | partitioned. |         | At that | point, the |           |          |           |             |            |      |
| ------------- | ------- | ---------- | ------------ | ------- | ------- | ---------- | --------- | -------- | --------- | ----------- | ---------- | ---- |
|               |         |            |              |         |         |            | algorithm | consists | of a pull | phase and a | subsequent | push |
| grid geometry | is      | rendered   | as in the    | regular | grid    | case. Due  |           |          |           |             |            |      |
phase.Thepullphaseiterativelycomputescoarserlevelsof
totheadaptivegrid,thisnewapproachhasbetterutilization
ofcomputationalresources,therebysignificantlyimproving theimagecontainingholes,forminganimagepyramid.Each
pixelinacoarserlevelistheaverageofthevalidpixelsin
thequality.
thecorrespondingfourpixelsfromthefinerlevel.Thepush
Yu et al. [YWY10] proposed a forward reprojection phasethenoperatesintheinverseorderandinterpolatesthe
methodthatleveragestheparalleldatascatteringfunction- holepixelsfromthecoarserlevels.Thisworksbestforthe
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2383
Load/Reuse
yes
| Lookup |     | Hit? no |     | Update |     |     |     |     |     |     |     |
| ------ | --- | ------- | --- | ------ | --- | --- | --- | --- | --- | --- | --- |
Recompute
Figure4: SchematicdiagramofapplyingtheRRCtoavoid
pixelshadingwheneverpossible[NSL*07].
smallholescausedbyper-pixelforwardreprojection.With
largerholes,theinterpolatedpixelsmayappearblurredand
canbeasourceofartefactsaswell.
3.4. Cacherefresh
Astraightforwardusageofdatareprojectionistoavoidshad-
| ing pixels | that are | visible in | the previous | frame. | This can |     |     |     |     |     |     |
| ---------- | -------- | ---------- | ------------ | ------ | -------- | --- | --- | --- | --- | --- | --- |
applytoeitherpartortheentirepixelshadingcomputation.
Forexample,ifweuseRRC,theoriginalpixelshadercan
bemodifiedtoaddacacheloadandreusebranch,asshown
inFigure4.Wheneachpixelpisgenerated,thereprojection
shaderfetchesthevalueatπ Figure5: Threecontrolflowstrategiesforacceleratingpixel
t−1 (p)inthecacheandtestsifthe
shadingusingtheRRC.
resultisvalid(i.e.acachehit).Ifso,theshadercanreusethis
valueinthecalculationofthefinalpixelcolour.Otherwise,
| the shader | executes | the normal | pixel shading. | Whichever |     |     |     |     |     |     |     |
| ---------- | -------- | ---------- | -------------- | --------- | --- | --- | --- | --- | --- | --- | --- |
routetheshaderfollows,italwaysstoresthecacheablevalue
ence,butmayleadtovisiblediscontinuityattileboundaries.
forpotentialreuseduringthefollowingframe. Therandomlydistributedrefreshstrategyupdatespixelsina
randompattern.Itexchangessharpdiscontinuitiesforhigh-
| Although   | a cached     | value | can be continuously |        | reused    |           |              |            |                     |     |      |
| ---------- | ------------ | ----- | ------------------- | ------ | --------- | --------- | ------------ | ---------- | ------------------- | --- | ---- |
|            |              |       |                     |        |           | frequency | noise, which | is usually | less objectionable. |     | Note |
| throughout | many frames, | it    | may quickly         | become | stale be- |           |              |            |                     |     |      |
thatitisrecommendedtoassignthesameIDtoeach2×2
causeofeithershadingchangesorresamplingerror.Nehab
|     |     |     |     |     |     | or larger | quad of pixels, | because | modern | GPUs | perform |
| --- | --- | --- | --- | --- | --- | --------- | --------------- | ------- | ------ | ---- | ------- |
etal.[NSL*07]proposedtorefresh(i.e.recompute)thevalue
|     |     |     |     |     |     | lock-step | shading computation |     | on such | quads. | The inter- |
| --- | --- | --- | --- | --- | --- | --------- | ------------------- | --- | ------- | ------ | ---------- |
periodicallyinordertocounteractthiseffect.Forafixedre-
leavedrefreshregionsareeasytoachievebyrenderinglow-
| fresh rate, | the screen | can be | divided into | (cid:3)n groups | and |     |     |     |     |     |     |
| ----------- | ---------- | ------ | ------------ | --------------- | --- | --- | --- | --- | --- | --- | --- |
resolutionframesandapplyingadistance-dependentoffset
updatedinaround-robinfashionineachframebytestingthe
onthegeometry.Fortemporalintegration,suchschemesare
followingconditionforeachpixel:
|     |     |                     |     |     |     | interesting,         | as the combination |     | of these samples |     | leads to a |
| --- | --- | ------------------- | --- | --- | --- | -------------------- | ------------------ | --- | ---------------- | --- | ---------- |
|     |     | (t+i)mod(cid:3)n=0, |     |     | (1) | high-resolutionshot. |                    |     |                  |     |            |
wherei isthegroupIDofthepixelandt
isaglobalclock. Inaddition,caremustbetakeninordertomaximizethe
Theysuggesttwosimplewaysofdividingthescreen: performancewhenimplementingthisschemewithRRC.The
|     |     |     |     |     |     | fact that | there are two | distinct | paths in Figure | 4,  | cache hit |
| --- | --- | --- | --- | --- | --- | --------- | ------------- | -------- | --------------- | --- | --------- |
• (cid:3)n andcachemiss,allowsforseveralimplementationalterna-
| The screen | is  | partitioned | into a grid | of  | non- |            |                      |     |          |              |     |
| ---------- | --- | ----------- | ----------- | --- | ---- | ---------- | -------------------- | --- | -------- | ------------ | --- |
|            |     |             |             |     |      | tives. The | most straightforward |     | approach | is to branch | be- |
overlappingtiles,withpixelsinatilesharingthesame
|     |     |     |     |     |     | tween the | two paths (Figure | 5a). | This allows | all | the tasks |
| --- | --- | --- | --- | --- | --- | --------- | ----------------- | ---- | ----------- | --- | --------- |
ID.
• Thescreenpixelsareequallypartitionedinto(cid:3)ngroups to be performed in a single rendering pass, but may suf-
|     |     |     |     |     |     | fer from | dynamic branching | inefficiency |     | particularly | when |
| --- | --- | --- | --- | --- | --- | -------- | ----------------- | ------------ | --- | ------------ | ---- |
witheachpixelassignedarandomgroupID.
|     |     |     |     |     |     | the refreshed | region is | not coherent | and | the branches | are |
| --- | --- | --- | --- | --- | --- | ------------- | --------- | ------------ | --- | ------------ | --- |
•
Theupdatedscreenpixelsareuniformlydistributedona unbalanced. To achieve better performance, Nehab et al.
regulargrid.Forastaticsceneandcamera,interleaving [NSL*07]defertheexpensiverecomputationandputitinto
nsuchimagesleadstoanaccuratehigh-resolutionimage
|     |     |     |     |     |     | a separate | pass so that | the branches | are | more | balanced |
| --- | --- | --- | --- | --- | --- | ---------- | ------------ | ------------ | --- | ---- | -------- |
ofthescene.
(Figure5b).Byrelyingonearly-Zculling,themissshader
|     |     |     |     |     |     | is only executed | on the | cache-miss | pixels | that | are auto- |
| --- | --- | --- | --- | --- | --- | ---------------- | ------ | ---------- | ------ | ---- | --------- |
With the tiled refresh strategy, pixels within a tile are re- matically grouped to avoid any performance penalty. If
freshedatthesametime.Thisleadstoexcellentrefreshcoher- the hit shader (green block in Figure 5) is also non-trivial
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2384 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
to compute, the branches in the first pass may still not be  1
 100
balanced.Sitthi-amornetal.[SaLY*08a]proposedamethod
Variance
Total fall-off
thatfurtherseparatesthispartofthecomputationintoathird  80  0.8
pass(Figure5c)inordertoreducedynamicbranchingcost.
Thisthree-passimplementationalsohastheadvantagethat semarF  60  0.6
oitaR
itdoesnotrequiremultiplerender-targetsupport,butincurs
moregeometryprocessingcost.Thechoiceofstrategythere-  40  0.4
| fore depends | on the relative | cost between | vertex | and pixel |     |     |     |     |     |     |      |
| ------------ | --------------- | ------------ | ------ | --------- | --- | --- | --- | --- | --- | --- | ---- |
|              |                 |              |        |           |  20 |     |     |     |     |     |  0.2 |
shadinginthetargetscene.Sitthi-amornetal.[SaLY*08a]
presentedsomeempiricalperformanceanalysisofthesethree
|                            |     |     |     |     |  0  |      |      |     |      |      |  0  |
| -------------------------- | --- | --- | --- | --- | --- | ---- | ---- | --- | ---- | ---- | --- |
| implementationsinpractice. |     |     |     |     |  0  |  0.2 |  0.4 |     |  0.6 |  0.8 |  1  |
α
3.5. Amortizedsampling
Figure6: Trade-offbetweentheamountofvariancereduc-
|     |     |     |     |     | tion (the | variance | ratio | curve), | and the | maximum | frames |
| --- | --- | --- | --- | --- | --------- | -------- | ----- | ------- | ------- | ------- | ------ |
Anothercommonstrategyofdatareuseistocombineprevi-
|     |     |     |     |     | of lag that | may | exist in | the current | estimate |     | (the total |
| --- | --- | --- | --- | --- | ----------- | --- | -------- | ----------- | -------- | --- | ---------- |
ousshadingresultswiththosefromthecurrentframe.Grad-
|     |     |     |     |     | falloff curve) | [NSL*07]. |     | This trade-off | is  | controlled | by the |
| --- | --- | --- | --- | --- | -------------- | --------- | --- | -------------- | --- | ---------- | ------ |
ualphase-outcanthenbeusedtoavoidexplicitlyrefreshing
parameterα.
| pixels. This | strategy is usually | applied | to amortize | the ex- |     |     |     |     |     |     |     |
| ------------ | ------------------- | ------- | ----------- | ------- | --- | --- | --- | --- | --- | --- | --- |
pensivetaskofcomputingaMonte-Carlointegral,inwhich
multiplespatialsamplesarecombinedforeachpixel.With
datafromthepast,eachframethenonlyneedstocomputea ingthesamplingratebyafactorof4.Ontheotherhand,the
lotlesssamples(typicallyonlyone)foreachpixelinorderto actualnumberofframescontributingtof withnon-trivial
t
achieveasimilarimagequality.Thisisbeneficialformany weights(i.e.largerthan8-bitprecision1/256)is10,which
high-qualityrenderingeffectsdescribedlater,suchasspatial
|     |     |     |     |     | indicates | that the | contribution | of  | any obsolete | sample | will |
| --- | --- | --- | --- | --- | --------- | -------- | ------------ | --- | ------------ | ------ | ---- |
anti-aliasing,softshadowsandglobalillumination. be smoothed out after 10 frames. This trade-off between
smoothnessandlagisillustratedinFigure6.Inpractice,α
Inordertoefficientlyreuseandcombinepreviouslycom-
mustbecarefullysettoobtainthebesttrade-off.
| puted samples | of a signal     | without | increasing  | storage over- |     |     |     |     |     |     |     |
| ------------- | --------------- | ------- | ----------- | ------------- | --- | --- | --- | --- | --- | --- | --- |
| head, Nehab   | et al. [NSL*07] | and     | Scherzer et | al. [SJW07]   |     |     |     |     |     |     |     |
proposedtocombineandstoreallpreviouslycomputedsam-
4. Data-ReuseQualityandPerformance
| ples associated | with a surfacepoint |     | using a | singlerunning |     |     |     |     |     |     |     |
| --------------- | ------------------- | --- | ------- | ------------- | --- | --- | --- | --- | --- | --- | --- |
average.Ineachframe,onlyonesamples t(p)iscomputed Theidealscenariofortakingadvantageofcoherenceiswhen
foreachpixelpandiscombinedwiththisrunningaverage thevalueofinterestobtainedfromapreviousframeisexactly
usingarecursiveexponentialsmoothingfilter: thesameasthedesiredone.Inreality,whenconsideringa
|     |     |     | (cid:2) | (cid:3) |     |     |     |     |     |     |     |
| --- | --- | --- | ------- | ------- | --- | --- | --- | --- | --- | --- | --- |
targetforreuse,weoftenfindthatitsvaluedependsonin-
| f t(p)←(α)s | t(p)+(1−α)f |     | π   | .   |     |     |     |     |     |     |     |
| ----------- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
t−1 t−1 (p) (2) putsthatarebeyondourcontrol.Thesemayincludechang-
ingviewingparameters,lightingconditions,timeitself,and
| Here,therunningestimateofframetisrepresentedbyf |     |     |     | tand |                   |     |                    |     |      |         |           |
| ----------------------------------------------- | --- | --- | --- | ---- | ----------------- | --- | ------------------ | --- | ---- | ------- | --------- |
|                                                 |     |     |     |      | most importantly, |     | user interactions. |     | Good | targets | for reuse |
isstoredintheRRC,ands
|     |     | t denotestheshadingcontribution |     |     |     |     |     |     |     |     |     |
| --- | --- | ------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
arethosethatchangelittleundertherangeofexpectedinput
fromthecurrentframe.Ifweexpandthisrecursiveformula-
variation.Nevertheless,evenslowlyvaryingattributesmust
tion,wecanseethattherunningestimateisequivalenttothe
beeventuallyupdated,andwemustalsoidentifyappropriate
weightedsumofalltheprevioussamplesatthesamesurface
refreshperiods.
point.Theweightofasinglesampledecreasesexponentially
overtime,andthesmoothingfactorαregulatesthetrade-off
Anotherimportantconsiderationisthecostofrecomputing
between the degree of variance reduction and responsive- eachreusedvalue.Thisisbecausetheoverheadassociated
nesstochangesinthesampledsignal.Forexample,asmall withobtainingpreviouslycomputedvaluesisnotnegligible
valueofαleadstoarelativelyslowdecreaseofthesample (seeSection3.1.1).Ifrecomputingavalueischeap,reusing
weights,whicheffectivelyaccumulatesmoresamplesinthe itmaynotbringanyperformanceadvantage.
pastandthereforeproducesasmootherresultattheexpense
Insummary,developersmustidentifycomputationallyex-
ofadditionallagintheshadedsignal.
pensiveintermediatecomputationsthatvarylittleunderthe
Theprecisedegreeofvariancereductionisgivenby rangeofexpectedinputchanges,anddeterminetheappro-
Var(f t(p)) α priate number of frames between updates. Given the large
|     |     | =   | .   |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
lim (3) number of different effects and input parameters involved
|     | t→∞ Var(s | t(p)) | 2−α |     |             |           |           |     |              |      |          |
| --- | --------- | ----- | --- | --- | ----------- | --------- | --------- | --- | ------------ | ---- | -------- |
|     |           |       |     |     | in a modern | real-time | rendering |     | application, | this | task can |
Forexample,choosingavalueofα=2/5reducesthevari- quickly become overwhelming. Recent efforts have there-
anceto1/4theoriginal.Thisisroughlyequivalenttoincreas- forefocusedonautomatingpartsofthisprocess.
|     |     |     |     |     |     |     |     |     | (cid:2)c | 2012TheAuthors |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | -------------- | --- |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2385
4.1. Semi-automatictargetidentification
| The    | system       | proposed | by              | Sitthi-amorn | et         | al. [SaLY*08b] |         |     |     |     |     |     |     |
| ------ | ------------ | -------- | --------------- | ------------ | ---------- | -------------- | ------- | --- | --- | --- | --- | --- | --- |
| starts | by analyzing |          | the source-code |              | of shaders | and            | identi- |     |     |     |     |     |     |
fyingpossibleintermediatecomputationsforreuse.Duringa
trainingsession,thesystemautomaticallyrendersanimation
| sequences | while | gathering |     | error and | performance | data | on  |     |     |     |     |     |     |
| --------- | ----- | --------- | --- | --------- | ----------- | ---- | --- | --- | --- | --- | --- | --- | --- |
shadersthathavebeenautomaticallymodifiedtocacheand
reuseeachcandidate.Therenderingsessionsaredesignedto
encompasstherangeoftypicalinputvariation,andarerun
underavarietyofdifferentrefreshperiods.
Assumingthattheinputvariationisstationary,theauthors
foundempiricalmodelsforboththeamountoferrorandthe
renderingcostassociatedtoreusingeachpossibleinterme-
diatevalue.Thesemodelswerelatershowntocloselymatch
measureddata.
|     |     |     |     |     |     |     |     | Figure 7: | Trade-off between | error | and | performance | asso- |
| --- | --- | --- | --- | --- | --- | --- | --- | --------- | ----------------- | ----- | --- | ----------- | ----- |
The expected error caused by reusing the value f of ciatedtocachingdifferentintermediateresultsinamarble
m
m (cid:3)n shader.Eachlineshowstheeffectofvaryingtherefreshpe-
| a given | intermediate |     | computation |     | over | a period | of  |     |     |     |     |     |     |
| ------- | ------------ | --- | ----------- | --- | ---- | -------- | --- | --- | --- | --- | --- | --- | --- |
riod(cid:3)nbetween2and50framesoneachchoiceofcached
framescanbemodelledbyaparametricequation:
|     |     |     |     |         |     |         |     | intermediatecomputation.Interestingerrorthresholds(cid:5) |     |     |     |     | iare |
| --- | --- | --- | --- | ------- | --- | ------- | --- | --------------------------------------------------------- | --- | --- | --- | --- | ---- |
|     |     |     |     | (cid:4) |     | (cid:5) |     |                                                           |     |     |     |     |      |
(cid:5)ˆ(f ,(cid:3)n)=α 1−e−λm((cid:3)n−1) . (4) marked,andtheresultsofwhichareshowninFigure8.Orig-
|     |     | m   |     | m   |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
inalshaderrunsat29FPS,asindicatedbythedashedline.
| Parametersα |     | m andλ | m canbeobtainedbyfittingthemodel |     |     |     |     |     |     |     |     |     |     |
| ----------- | --- | ------ | -------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
todatagatheredinthetrainingsession.
Figure8showstheresultsofrenderingundereachchoiceof
errortolerance,intermsofbothqualityandperformance.As
Modellingthecostofrenderingeachpixelrequiresmore
theuserselectslargererrorthresholds,thesystemreactsby
work.First,thesystemsolvesforanestimateoftheaverage
selectinglargerportionsofthecomputationforcaching(see
timetakentorenderapixelunderbothcache-hitandcache-
|      |             |        |       |     |               |             |        | t h e p a y l o | a d ), e v e n tu a ll y | i n c lu d   | i n g ev e n | t h e vi e w -    | d e p en d e n t |
| ---- | ----------- | ------ | ----- | --- | ------------- | ----------- | ------ | --------------- | ------------------------ | ------------ | ------------ | ----------------- | ---------------- |
| miss | conditions. | Denote | these | by  | (cid:3) (f m) | and (cid:3) | (f m), |                 |                          |              |              |                   |                  |
|      |             |        |       |     | hit           | miss        |        |                 |                          |              |              |                   |                  |
|      |             |        |       |     |               |             |        | l ig h ti n g , | a t w h i c h p o in t   | u n d e s ir | a b le a rt  | ef a c ts a p p e | a r. N e v e r-  |
respectively.Thesevaluesareobtainedbysolvinganover-
constrainedlinearsystemfor(cid:3) (f m)and(cid:3) (f t h e le ss , su b st a n t i a l p e r f o rm a n c e i m p r o v em e n t s ar e p o s s i b le
|     |     |     |     | hit |     | miss m): |     |              |                            |             |            |                |                 |
| --- | --- | --- | --- | --- | --- | -------- | --- | ------------ | -------------------------- | ----------- | ---------- | -------------- | --------------- |
|     |     |     |     |     |     |          |     | b e lo w a n | a cc e p t a b l e e r r o | r th re s h | o l d( s e | e e r u n n in | g a t a 2 . 8 × |
3
|     | H   | (cid:3) (f m)+M |     | (cid:3) (f | m)+c=(cid:3)t | .   | (5) | improvement). |     |     |     |     |     |
| --- | --- | --------------- | --- | ---------- | ------------- | --- | --- | ------------- | --- | --- | --- | --- | --- |
|     |     | i hit           |     | i miss     |               | i   |     |               |     |     |     |     |     |
Eachequationcomesfrommeasurementsofdifferentframes
|      |              |           |     |         |               |           |     | 4.2. Reprojectionerrorsandtheiraccumulation |     |     |     |     |     |
| ---- | ------------ | --------- | --- | ------- | ------------- | --------- | --- | ------------------------------------------- | --- | --- | --- | --- | --- |
| i in | the training | sequence. |     | Here, c | is a constant | rendering |     |                                             |     |     |     |     |     |
overhead,H iisthenumberofhits,M ithenumberofmisses Thestrategiesweusetoobtainthevaluesofpreviouscom-
and(cid:3)t thetimetorenderframei. putations (see Section 3) can themselves inject unwanted
i
errors.Althoughsucherrorsareindirectlymodelledbythe
Theaveragecostofrenderingasinglepixelcanthenbe
automaticmethoddescribedabove,herewepresentasim-
modelledas
plifiedanalysisofthisspecificissue(see[YNS*09]foran
alternative,moredetailedpresentation).
| rˆ(f | ,(cid:3)n)=λ((cid:3)n)(cid:3) |     |     | (f m)+(1−λ((cid:3)n))(cid:3) |     | (f   | m),(6) |     |     |     |     |     |     |
| ---- | ----------------------------- | --- | --- | ---------------------------- | --- | ---- | ------ | --- | --- | --- | --- | --- | --- |
|      | m                             |     | hit |                              |     | miss |        |     |     |     |     |     |     |
whereλ((cid:3)n)=μ(1−1/(cid:3)n)isanempiricalmodelforthe Duetocameraandobjectmotions,thecorrespondingpo-
sitionsofanygivensurfacepointintwoconsecutiveframes
cachehit-rateasafunctionof(cid:3)n,andμisobtainedbyfitting
generallyinvolvenon-integercoordinatesinatleastoneof
thismodeltothetrainingdata.
|     |     |     |     |     |     |     |     | them. Reprojection | strategies | must | therefore | resample | any |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------ | ---------- | ---- | --------- | -------- | --- |
datathataremovedbetweenframes.Bilinearfilteringis,by
| Using | these | models, | the | system | allows | the developer | to  |     |     |     |     |     |     |
| ----- | ----- | ------- | --- | ------ | ------ | ------------- | --- | --- | --- | --- | --- | --- | --- |
specify a target average pixel error. It then automatically far, the most commonly used resampling strategy in real-
selects the shader component that provides the greatest time reprojection applications. Mappings between consec-
improvement in performance without exceeding the error utive real-time frames tend to exclude large minifications,
threshold. makingtrilinearfilteringunnecessary.Itisthereforeimpor-
tanttounderstandtheimpactofbilinearfilteringonthequal-
| Figure | 7   | shows the | error/performance |     | behaviour |     | associ- |     |     |     |     |     |     |
| ------ | --- | --------- | ----------------- | --- | --------- | --- | ------- | --- | --- | --- | --- | --- | --- |
ityofreprojecteddata.
| ated | with caching | several |     | different | intermediate | computa- |     |     |     |     |     |     |     |
| ---- | ------------ | ------- | --- | --------- | ------------ | -------- | --- | --- | --- | --- | --- | --- | --- |
tionsperformedbyamarbleshader.Thisshadercombinesa Although analyzing the effect of general motion across
marble-likealbedomodelledasfiveoctavesofa3DPerlin multiple frames is impractical, the special case of con-
noise function, with a simple Blinn–Phong specular layer. stant panning motion is easy to describe mathematically,
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2386 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
Figure8: ResultsofselectingdifferenterrorthresholdsinFigure7.Theintermediatevalueselectedforcaching(payload)is
shownnexttothefinalrenderedresults(finalshading).Highererrorthresholdsallowforsubstantialpartsofthecomputation
tobecached,leadingtobetterperformanceattheexpenseofquality.
| particularly | in one dimension | (other | types | of motion | can |     |     |     |     |     |     |
| ------------ | ---------------- | ------ | ----- | --------- | --- | --- | --- | --- | --- | --- | --- |
beapproximatedbytranslation,atleastlocally).
Assumewehaveinformationstoredinaframef
t thatwe
wanttoresampletotimet+1.Constantpanningmotionwith
| velocity v | can be described | by  | π t+1 (p)=p−v, | for | every |     |     |     |     |     |     |
| ---------- | ---------------- | --- | -------------- | --- | ----- | --- | --- | --- | --- | --- | --- |
pointp andtimet.Withoutlossofgenerality,assumethat
thevelocityisin[−0.5,0.5].Theentireresamplingoperation
canberephrasedintermsofthediscreteconvolution
|     |         | (cid:6) | (cid:7) |     |     |     |     |     |     |     |     |
| --- | ------- | ------- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
|     | f t→t+1 | =f t ∗  | v (1−v) |     | (7) |     |     |     |     |     |     |
|     |         | =f ∗k   | ,       |     | (8) |     |     |     |     |     |     |
t v
|                                                    |                   |     |              |     |         | Figure 9:        | Amplitude   | response               | and phase | error     | associated |
| -------------------------------------------------- | ----------------- | --- | ------------ | --- | ------- | ---------------- | ----------- | ---------------------- | --------- | --------- | ---------- |
|                                                    |                   |     |              |     |         | with translation |             | by linear re-sampling. |           | Note that | largest    |
| where we                                           | used the notation | f   | to represent |     | the new |                  |             |                        |           |           |            |
|                                                    |                   |     | t→t+1        |     |         | amplitude        | attenuation | and phase              | error     | happen    | for high   |
| framecontainingonlyreprojecteddata.Underourassump- |                   |     |              |     |         | frequencies.     |             |                        |           |           |            |
tions,thebehaviourofreprojectionisthereforecontrolledby
| theeffectoftheconvolutionkernelk |     |     | =[v | (1−v)]. |     |     |     |     |     |     |     |
| -------------------------------- | --- | --- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
v
|     |     | v,  |     |     | ω,  |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
For each different velocity and for each frequency The distribution has a variance of σ2=v(1−v). Repeat-
wecomputetheamplitudeattenuationandthephaseerrorin- edlyconvolvingk
vwithitselfamountstocomputingthesum
| troducedbyk | v.ResultingplotsareshowninFigure9,where |     |     |     |     |     |     |     |     |     |     |
| ----------- | --------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
distribution.BytheCentralLimitTheorem,thisquicklycon-
| shaded regions | represent | values | between the | extremes. | As  |     |     |     |     |     |     |
| -------------- | --------- | ------ | ----------- | --------- | --- | --- | --- | --- | --- | --- | --- |
vergestoaGaussian.Bythesumpropertyofvariance,we
canbeseenfromtheplots,reprojectionthroughbilinearre-
haveσ2=nv(1−v).Theprogressivelylow-passnatureof
n
samplingtendstoattenuateandmisplacehighfrequencies. repeated resampling then becomes obvious in the formula
Notvisiblefromtheplotisthefactthattheproblemispartic-
forthevariance.
ularlyextremewhenv=±0.5andthatitdisappearswhen
v=0(asexpectedfromtheinterpolationproperty). Thereareseveralalternativestopreventtheexcessiveblur
introducedbyrepeatedresamplingfromcausingobjection-
Theeffectofrepeatedresamplingcanalsobeanalyzed: able rendering artefacts. For example, we can periodically
f =f ∗k recompute values instead of relying on reprojection. This
|     | t→t+n | t→t+n−1 | v   |     | (9) |              |              |          |     |              |        |
| --- | ----- | ------- | --- | --- | --- | ------------ | ------------ | -------- | --- | ------------ | ------ |
|     |       |         |     |     |     | is, in fact, | the approach | followed | by  | Sitthi-amorn | et al. |
[SaLY*08b](Section3.4).Anotheralternativeistoreplace
nin(cid:9)(cid:10)total bilinearresamplingwithanalternativestrategythathasbet-
|     |     | (cid:8) | (cid:11) |     |     |     |     |     |     |     |     |
| --- | --- | ------- | -------- | --- | --- | --- | --- | --- | --- | --- | --- |
=f ∗(k ∗···∗k v). terfrequencyproperties,suchastheoneproposedbyYang
|     |     | t v |     |     | (10) |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- |
etal.[YNS*09](Section5.3).Finally,inthecontextofcom-
putationamortizationdescribedinSection3.5,wecanalso
| The trick           | is to interpret | k as | the probability | mass        | func- |               |           |                  |     |          |         |
| ------------------- | --------------- | ---- | --------------- | ----------- | ----- | ------------- | --------- | ---------------- | --- | -------- | ------- |
|                     |                 | v    |                 |             |       | progressively | attenuate | the contribution |     | of older | frames, |
| tion of a Bernoulli | distribution    |      | with success    | probability | v.    |               |           |                  |     |          |         |
therebylimitingthemaximumamountofvisibleblur.
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2387
Table 1: Existing approaches that exploit TC in real-time rendering, indexed by applications (rows) and the types of techniques applied
(columns),withsectionnumbersofthissurveyifapplicable.
|     |     | Reverse      | Forward      |     | Handling     | Cache   | Amortized | TCtarget       | Reprojection |       |     |     |     |
| --- | --- | ------------ | ------------ | --- | ------------ | ------- | --------- | -------------- | ------------ | ----- | --- | --- | --- |
|     |     | reprojection | reprojection |     | disocclusion | refresh | sampling  | identification |              | error |     |     |     |
Application (3.1) (3.2) (3.3) (3.4) (3.5) (4.1) (4.2) Object-space Post-processing
| Pixelshader |     | [NSL*07] |     |     |     | [SaLY*08b] |     | [SaLY*08b] |     |     |     |     |     |
| ----------- | --- | -------- | --- | --- | --- | ---------- | --- | ---------- | --- | --- | --- | --- | --- |
acceleration(5.1)
| Multi-pass   |     | [NSL*07] | [AH93] |     |     |     | [NSL*07] |     |     |     |     | [HDMS03] |     |
| ------------ | --- | -------- | ------ | --- | --- | --- | -------- | --- | --- | --- | --- | -------- | --- |
| effects(5.2) |     |          | [CW93] |     |     |     |          |     |     |     |     |          |     |
[YWY10]
[DRE*10]
| Shading |     | [YNS*09] |     |     |     | [YNS*09] | [YNS*09] |     | [YNS*09] |     |     |     |     |
| ------- | --- | -------- | --- | --- | --- | -------- | -------- | --- | -------- | --- | --- | --- | --- |
anti-aliasing(5.3)
| Shadows(5.4) |     | [SJW07] |     |     |     |     | [SJW07] |     |     |     |     |     |     |
| ------------ | --- | ------- | --- | --- | --- | --- | ------- | --- | --- | --- | --- | --- | --- |
[SSMW09]
| Global            |     | [KTM*10] |     |     |     |     | [MSW10] |     |     |     | [LSK*07] |     |     |
| ----------------- | --- | -------- | --- | --- | --- | --- | ------- | --- | --- | --- | -------- | --- | --- |
| Illumination(5.5) |     | [MSW10]  |     |     |     |     |         |     |     |     | [REH*11] |     |     |
| Spatio-temporal   |     | [HEMS10] |     |     |     |     |         |     |     |     |          |     |     |
upsampling(5.6)
| Frame                |     | [YTS*11] | [DER*10b] |     | [And10] |     |     |     |     |     |          |          |     |
| -------------------- | --- | -------- | --------- | --- | ------- | --- | --- | --- | --- | --- | -------- | -------- | --- |
| interpolation(5.7)   |     | [And10]  | [YTS*11]  |     |         |     |     |     |     |     |          |          |     |
| Non-photorealistic   |     |          | [LSF10]   |     |         |     |     |     |     |     |          | [BFP*11] |     |
| rendering(5.8)       |     |          | [LSF10]   |     |         |     |     |     |     |     |          | [BFP*11] |     |
| Level-of-detail(5.9) |     | [SW08]   |           |     |         |     |     |     |     |     | [HREB11] |          |     |
| Streaming(5.10)      |     | [PHE*11] |           |     |         |     |     |     |     |     | [FE09]   | [FB08]   |     |
| Onlinevisibility     |     |          |           |     |         |     |     |     |     |     | [GKM93]  |          |     |
| culling(5.11)        |     |          |           |     |         |     |     |     |     |     | [ZMHI97] |          |     |
[BWPP04]
[MBW08]
| Temporal         |     |     |     |     |     |     |     |     |     |     |     | [DER*10a] |     |
| ---------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --------- | --- |
| perception(5.12) |     |     |     |     |     |     |     |     |     |     |     | [TDR*11]  |     |
5. Applications
| There are | numerous | applications |     | in real-time |     | rendering |     |     |     |     |     |     |     |
| --------- | -------- | ------------ | --- | ------------ | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
whereTCcanbeexploitedtoimprovetheperformanceand
| quality. In | this section, | we   | aim to     | summarize | the     | available |     |     |     |     |     |     |     |
| ----------- | ------------- | ---- | ---------- | --------- | ------- | --------- | --- | --- | --- | --- | --- | --- | --- |
| techniques  | that follow   | this | direction. | Table     | 1 lists | all the   |     |     |     |     |     |     |     |
relevantapproachesthatwedescribe,categorizedbytheap-
plicationandthetypeoftechniquesapplied.Manyofthese
applicationsarebasedonimage-basedreprojectionandre-
latedapproaches(Section3).Performanceandqualitystud- Figure10: Additionalexamplesofshadingaccelerationus-
ingRRC.Eachimagecompares(top)aninputpixelshader
ies(Section4),whichwereoriginallydiscussedinthecon-
to(bottom)aversionmodifiedtocachesomepartialshading
textofpixelshadingaccelerationandanti-aliasing,canalso
|     |     |     |     |     |     |     | computations | over | consecutive | frames. | The | shading | error |
| --- | --- | --- | --- | --- | --- | --- | ------------ | ---- | ----------- | ------- | --- | ------- | ----- |
behelpfulinoptimizingRRC-basedtechniques.Inaddition,
thereareseveralmethodsthatemployanobjectspaceora afterapplyingthecacheisillustratedintheinsetimages.
post-processingtypeofdatareuse,whicharealsorelevantto
InadditiontothemarbleshaderdescribedinSection4.1,
thetopicanddiscussedinthissurvey.
|     |     |     |     |     |     |     | we show | two more  | results | of accelerating |     | expensive    | pixel |
| --- | --- | --- | --- | --- | --- | --- | ------- | --------- | ------- | --------------- | --- | ------------ | ----- |
|     |     |     |     |     |     |     | shaders | using the | RRC     | [SaLY*08b].     | The | first shader | is    |
5.1. Pixelshaderacceleration
|     |     |     |     |     |     |     | a Trashcan | environmental |     | reflection | shader | from | ATI’s |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ------------- | --- | ---------- | ------ | ---- | ----- |
One of the direct uses of the RRC is to accelerate ex- Toyshop demo, which combines a simple base geometry
pensive pixel-shading computations [NSL*07, SaLY*08a, with a high-resolution normal map and environment map
SaLY*08b]. The basic idea is to bypass part or all of the toreproducetheappearanceofashinytrashcan.Theshader
computationoftheoriginalpixelshaderwheneverthereare combines 25 stratified samples of an environment map us-
previousshadingresultsavailableinthecache,asdescribed ingaGaussiankerneltoattenuatealiasingartefacts.Inthis
inSection3.4.Figure4showstheflowchartofthistypeof example, we found that caching the sum of 24 samples of
shadingacceleration. the possible 25 gives the most effective speedup without
|     |     |     |     |     |     |     |     |     |     |     | (cid:2)c | 2012TheAuthors |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | -------------- | --- |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2388 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
introducingtoomanyvisibleartefacts(seeFigure10(left) Theextenttowhichperformanceisimproveddependsonthe
foracomparison).Inotherwords,themodifiedshaderevalu- relativecostbetweenrenderingthecentralframe(geometry+
ates24sampleseveryfourthframe(onaverage)andevaluates shading)andrenderingeachaccumulatedframe(geometry+
thesinglesamplewiththegreatestreconstructionweightat cache-lookup).Thisisbecausereversereprojectionrequires
every frame. Indeed, this shader is not particularly suited rasterizing the geometry of each accumulated frame (see
for using TC to accelerate, because all of the calculations Section3.1).Improvementsarethereforelimitedwhenge-
depend strongly on the camera position and cached values ometryiscomplexandshadingisrelativelysimple.Yuetal.
2.1×
quickly become stale. Nevertheless, RRC provides a [YWY10]proposedtouseforwardreprojection(Section3.2)
performanceimprovementatanacceptableleveloferror. inordertodecouplethisoverheadfromgeometrycomplex-
ity.Theyalsoapplyablurringpasstothereprojectedframes
| The second | shader | computes |     | approximate | object-space |     |     |     |     |     |     |     |     |
| ---------- | ------ | -------- | --- | ----------- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- |
beforeaccumulationsothattheundersamplinganddisocclu-
ambientocclusionateachpixelforachessboardscenewith sionartefactsareattenuated.
thekingpiecemovingandtheremainingpiecesstatic.The
basicideaistoapproximatethescenegeometryasacollec- Anotherrenderingscenariothatiscloselyrelatedtodepth-
tion of discs organized in a hierarchical data structure and of-fieldisstereographicrendering.Twoviewsarerendered
storedasatexture.Aseachpixelisshaded,thisdatastructure fromthesamescene,onefromtheviewpointofeacheyeof
istraversedtocomputethepercentageofthehemispherethat a virtual observer. Then, one of many different methods is
isoccluded.Thiscalculationiscombinedwithadiffusetex- usedtoexposeeachoftheuser’seyestothecorresponding
tureandaBlinn–Phongspecularlayertoproducethefinal image(e.g.shutterglassesandpolarizationfilters),leading
colour. In this particular scene, the ambient-occlusion cal- totheperceptionofdepth.Stereographicrenderinghasre-
culation is carried out by summing the contribution of the cently gained increased attention given the success of 3D
kingchesspieceseparatelyfromtheotherpieces.Wefound cinematographicproductionsaswellastheincreasedavail-
that caching the portion of the ambient-occlusion calcula- abilityof3D-capableconsumerhardware(TVsets,portable
tion that accounts for only the static pieces gives the best video-gameconsoles,etc.).
result.Inotherwords,thecontributionofthemovingking
|                   |     |         |                |     |          |        | One way | to avoid | the | doubling | of cost-per-frame |     | that |
| ----------------- | --- | ------- | -------------- | --- | -------- | ------ | ------- | -------- | --- | -------- | ----------------- | --- | ---- |
| and the remaining |     | shading | are recomputed |     | at every | frame. |         |          |     |          |                   |     |      |
This provides an 8× speedup for a marginal amount error wouldresultfromthebrute-forceapproachtostereographic
renderingistoinsteadrenderonlyoneframefromthestereo
andisdemonstratedinFigure10(right).Cachingmorecom-
pairandthenwarpittoproducetheotherframe.Thisisa
putations,suchastheentireambient-occlusioncalculation,
well-establishedideathatwassuccessfullyusedinthecon-
willleadtovisibleerrorintheresult,althoughthespeedup
|     |     |     |     |     |     |     | text of stereographic |     | ray-tracing | [AH93] | (where | rendering |     |
| --- | --- | --- | --- | --- | --- | --- | --------------------- | --- | ----------- | ------ | ------ | --------- | --- |
factorwillalsobelarger(15×ormore).
costwasextremelyhigh)andinstereographichead-tracked
displays[MB95](wherewarpingwasusedtoefficientlyup-
5.2. Multi-passeffects dateapreviouslyrenderedstereopairtocompensateforuser
headmovements).
Effectssuchasmotionbluranddepth-of-fieldaremosteas-
ilyunderstoodandimplementedastheaccumulationofase- Sinceper-pixeldepthinformationisanaturalby-product
riesofframes,respectively,renderedunderslightvariations ofreal-timerendering,generatingthemappingbetweentwo
in animation time or camera position, relative to a central stereo views is particularly easy. The challenges are in the
designofanefficientwarpingprocedurethatadaptstosharp
frame[HA90].Althoughrenderingandaccumulatingmul-
tipleframesinordertoproduceasingleoutputframemay features and attenuates any artefact resulting from surface
seemprohibitivelyexpensive,thesmallmagnitudeofvari- pointsthatareonlyvisiblefromoneoftheviewpoints.
ationininputparametersbetweeneachaccumulatedframe
Onewaytoperformthisoperationistorelyonanadaptive
| leads to large | amounts | of  | coherence | between | them. | This |     |     |     |     |     |     |     |
| -------------- | ------- | --- | --------- | ------- | ----- | ---- | --- | --- | --- | --- | --- | --- | --- |
warpinggrid[DRE*10](seeSection3.2)totransformone
| coherence | has been | successfully |     | exploited | in the | context |     |     |     |     |     |     |     |
| --------- | -------- | ------------ | --- | --------- | ------ | ------- | --- | --- | --- | --- | --- | --- | --- |
viewintoanother.Didyketal.furtherproposedtoexploitTC
ofimage-basedrendering[CW93],ray-tracedanimationse-
|     |     |     |     |     |     |     | by analyzing | the | camera movement |     | from one | frame | to the |
| --- | --- | --- | --- | --- | --- | --- | ------------ | --- | --------------- | --- | -------- | ----- | ------ |
quences[HDMS03],andmorerecentlyinreal-timerender-
next.Dependingonthecameramovementandthepreviously
ing[NSL*07,YWY10].Imperfectionstendtobehiddenby
computedframe,itcanbemoreadvantageoustorenderand
thelow-passnatureoftheseeffects,leadingtoimagesthat
|                                                    |                   |     |      |                 |     |          | then warp    | either    | the left or | the right | eye view. | For          | exam-   |
| -------------------------------------------------- | ----------------- | --- | ---- | --------------- | --- | -------- | ------------ | --------- | ----------- | --------- | --------- | ------------ | ------- |
| are virtually                                      | indistinguishable |     | from | the brute-force |     | results. |              |           |             |           |           |              |         |
|                                                    |                   |     |      |                 |     |          | ple, imagine | a panning | motion      | from      | left to   | right. Here, | a       |
| Thesavingsinrenderingcostcanbeusedtoeitherincrease |                   |     |      |                 |     |          |              |           | i           |           |           |              |         |
|                                                    |                   |     |      |                 |     |          | right-eye    | view in   | frame       | might be  | very      | close to     | a left- |
qualitybyraisingthenumberofaccumulatedframes,orto
|     |     |     |     |     |     |     | eye view | in frame | i+1. | Consequently, | it  | makes sense | to  |
| --- | --- | --- | --- | --- | --- | --- | -------- | -------- | ---- | ------------- | --- | ----------- | --- |
increasetheframerateforafixed-qualitysetting.
|               |          |     |          |             |     |           | render the | right        | eye view | in frame    | i+1. | The rendered |         |
| ------------- | -------- | --- | -------- | ----------- | --- | --------- | ---------- | ------------ | -------- | ----------- | ---- | ------------ | ------- |
|               |          |     |          |             |     |           | frame and  | the previous | are      | then warped | to   | produce      | a left- |
| The real-time | approach |     | proposed | in [NSL*07] |     | starts by |            |              |          |             |      |              |         |
i+1.
completely rendering a central frame into a buffer. Then, eye view for frame In particular, for a static camera
whenrenderingtheaccumulatedframes,shadinginformation and scene, the result is indistinguishable from a two-view
| is obtained | from | the central | frame | by reverse | reprojection. |     | rendering. |     |     |     |     |     |     |
| ----------- | ---- | ----------- | ----- | ---------- | ------------- | --- | ---------- | --- | --- | --- | --- | --- | --- |
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2389
| Figure 11: | Sampling        | from | multiple | sub-pixel | buffers. To  |     |     |     |     |     |     |
| ---------- | --------------- | ---- | -------- | --------- | ------------ | --- | --- | --- | --- | --- | --- |
| properly   | reconstruct     | the  | quadrant | value,    | Yang et al.  |     |     |     |     |     |     |
| [YNS*09]   | use non-uniform |      | blending | weights   | defined by a |     |     |     |     |     |     |
tentfunctioncentredonthequadrantbeingupdated.(a)In
|     |     |     |     |     |     | Figure12: | Comparisonbetweennoanti-aliasing,amortized |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --------- | ------------------------------------------ | --- | --- | --- | --- |
theabsenceoflocalmotion,onlythecorrectpixelhasnon-
supersamplingwithviewportsizecache(Amort1×),amor-
| zeroweightinthetent,sonore-samplingblurisintroduced. |     |     |     |     |     |                     |     |               | 2×2 |           |         |
| ---------------------------------------------------- | --- | --- | --- | --- | --- | ------------------- | --- | ------------- | --- | --------- | ------- |
|                                                      |     |     |     |     |     | tized supersampling |     | with improved |     | sub-pixel | buffers |
(b)Foramovingscene,thesamplesareweightedusingthe (Amort4×)andtheground-truthreferenceresultforahorse-
tentfunction,andhigherweightsaregiventosamplescloser
checkerboardscene[YNS*09].The4×‘still’image(without
tothedesiredquadrantcentretolimittheamountofblur.
|     |     |     |     |     |     | animation) | approaches | the quality | of  | the reference | result, |
| --- | --- | --- | --- | --- | --- | ---------- | ---------- | ----------- | --- | ------------- | ------- |
whereastheanimatedresultprovidesanacceptableapprox-
| 5.3. Shadinganti-aliasing |            |              |     |           |          | imationwithoutoverblurring. |     |     |     |     |     |
| ------------------------- | ---------- | ------------ | --- | --------- | -------- | --------------------------- | --- | --- | --- | --- | --- |
| One of                    | the direct | applications | of  | amortized | sampling |                             |     |     |     |     |     |
introduced.Italsocorrectlyhandlesbothstaticandmoving
| (Section | 3.5) is to | supersample | procedural | shading | effects, |     |     |     |     |     |     |
| -------- | ---------- | ----------- | ---------- | ------- | -------- | --- | --- | --- | --- | --- | --- |
which usually contain high-frequency components that are scenessimultaneously.
prone to aliasing artefacts. By accumulating jittered sam- Inadditiontothehigherresolutionbuffer,empiricalmeth-
plesgeneratedinpreviousframesusingamortizedsampling, odsareusedtoestimatereconstructionerrorsaswellasthe
the extra frequency bands can be effectively suppressed. amountofsignalchangeinrealtime,andlimitαaccordingly
However,supersamplingusuallyrequiresasmallexponen-
suchthataminimumamountofrefreshisguaranteed.The
tialsmoothingfactorαinordertogathersufficientsamples.
|     |     |     |     |     |     | reconstruction | error | is estimated | by  | deriving an | empirical |
| --- | --- | --- | --- | --- | --- | -------------- | ----- | ------------ | --- | ----------- | --------- |
Thishastheundesiredsideeffectthattherunningestimate relationship between the fractional pixel velocity v, α and
canbeoverblurredbecauseofexcessiverepeatedresampling theerror.Signalchange,ontheotherhand,isestimatedby
ofthecache(Section4.2).
asmoothedresidualbetweenthealiasedsampleandthehis-
toryvalue.Theusersetsthresholdsforbotherrors,andthe
Yangetal.[YNS*09]proposedtokeepahigherresolution
(2×2)runningaverageinordertocounteractthisoverblur- boundsforαarecomputedbasedontheerrorvalues.
ringartefact.Toreducetheoverheadofmaintainingsucha Figure12showstheresultofapplyingamortizedsampling
high-resolutionbuffer,theystorethe2×2quadrantsamples
toanti-aliasingahorse-checkboardscene,whichincludesan
| ofeachpixelintofoursub-pixelbuffers{b |     |     |     | },k∈{0,1,2,3} |     |                                                  |     |     |     |     |     |
| ------------------------------------- | --- | --- | --- | ------------- | --- | ------------------------------------------------ | --- | --- | --- | --- | --- |
|                                       |     |     |     | k             |     | animatedwoodenhorsegallopingoveramarblecheckered |     |     |     |     |     |
usingtheinterleavedsamplingscheme.Eachsub-pixelbuffer floor. The result using 2×2 sub-pixel buffers shows sig-
isscreensizedandmanagesonequadrantofapixel.These nificantimprovementoverregularamortizedsampling(1×
sub-pixel buffers are updated in a round-robin fashion, i.e. viewport-sizedcache),withonlyaminorsacrificeofspeed.
onlyoneperframe.
Infact,thePSNRshowsthatthistechniqueoffersbetterqual-
itythanconventional4×4stratifiedsupersampling,which
Reconstructingasub-pixelvaluefromthefoursub-pixel
runsatasixtimeslowerframerate.
buffersinvolvesmorework.Notethatintheabsenceofscene
motion,thesefoursub-pixelbufferseffectivelyformahigher
| resolution | framebuffer. | However, | under | scene | motion, the |     |     |     |     |     |     |
| ---------- | ------------ | -------- | ----- | ----- | ----------- | --- | --- | --- | --- | --- | --- |
5.4. Shadows
| sub-pixel | samples | computed | in earlier | frames | reproject to |     |     |     |     |     |     |
| --------- | ------- | -------- | ---------- | ------ | ------------ | --- | --- | --- | --- | --- | --- |
offsetlocations.Conceptually,Yangetal.[YNS*09]forward Shadowsarewidelyacknowledged tobeoneoftheglobal
reprojectalltheprevioussamplesintothecurrentframeand lighting effects with the most impact on scene perception.
computeaweightedsumofthesesamplesusingatentker- Theyareperceivedasanaturalpartofasceneandgiveimpor-
nel, as indicated in Figure 11. This effectively reduces the tantcuesaboutthespatialrelationshipofobjects.Thefield
contributionofdistantsamplesandlimitstheamountofblur of shadow algorithms is vast and many different methods
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2390 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
|     |     |     |     |     |     |     | Figure 14: | Shadow | adaption | over | time of | an undersam- |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ------ | -------- | ---- | ------- | ------------ |
pleduniformshadowmapafter0(top-left),1(top-middle),
Figure13: Iftherasterizationoftheshadowmapchanges 10(top-right),20(bottom-left),30(bottom-middle)and60
| (here represented |     | by a right | shift), | the shadowing |     | results |     |     |     |     |     |     |
| ----------------- | --- | ---------- | ------- | ------------- | --- | ------- | --- | --- | --- | --- | --- | --- |
(bottom-right)frames.
mayalsochange.Ontheleft,threefragmentsareinshadow,
whileontheright,fivefragmentsareinshadow.Thisresults
inflickeringorswimmingartefactsinanimations.
| exist. Several | surveys  | [HLHS03, |                | SWP11], |            | courses |     |     |     |     |     |     |
| -------------- | -------- | -------- | -------------- | ------- | ---------- | ------- | --- | --- | --- | --- | --- | --- |
| [EASW09,       | EASW10], | and      | books [ESAW11] |         | illustrate | nu-     |     |     |     |     |     |     |
merousapproachestoaddressthisimportantproblem.
|     |     |     |     |     |     |     | Figure 15: | Light-space |     | perspective | shadow | mapping |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ----------- | --- | ----------- | ------ | ------- |
Duetoitsspeedandversatility,shadowmappingisoneof [WSP04](left)givesgoodresultsforashadowmapresolu-
tionof10242andaviewportof1680×1050,buttemporal
themostusedreal-timeshadowingapproaches.Theideaisto
reprojection(middle)canstillgivesuperiorresultsbecause
firstcreateadepthimageofthescenefromthepointofview
itusesshadowtestconfidence,definedbythemaximumnorm
| of the light | source | (shadow | map). | This image | encodes | the |     |     |     |     |     |     |
| ------------ | ------ | ------- | ----- | ---------- | ------- | --- | --- | --- | --- | --- | --- | --- |
frontbetweenlitandunlitpartsofthescene.Onrendering ofshadowmaptexelcentreandcurrentpixel(right).
thescenefromthepointofviewofthecamera,eachfrag-
mentistransformedintothisspace.Here,thedepthofeach
resultsintemporalaliasingartefacts,mainlyflickering(See
transformedcamerafragmentiscomparedtotherespective
Figure13).
depthintheshadowmap.Ifthedepthofthecamerafragment
isnearer,itisconsideredlit,otherwiseitisinshadow(see Themainideain[SJW07]istojittertheviewportofthe
Figure13).
|     |     |     |     |     |     |     | shadow map | differently | in  | each frame | and to | combine the |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ----------- | --- | ---------- | ------ | ----------- |
resultsoverseveralframes,leadingtoahighereffectiveres-
olution.Figure14showsthegradualrefinementafteraccu-
5.4.1. Pixel-correctshadows mulatingresultsfrommultipleframes.
The most concerning visual artefacts of shadow mapping ExponentialsmoothingasdescribedinSection3.5isem-
originatefromaliasingduetoundersampling.Thecausefor ployedhereontheshadowmaptestss t[p].Thisservesadual
undersamplingis,inturn,closelyrelatedtotherasterization purpose.Ontheonehand,temporalaliasingcanbereduced
that is used to create the shadow map itself. Rasterization by using a small smoothing factor α. On the other hand,
samplesprimitivesonaregulargrid.Eachfragmentiscentred the shadow quality can actually be made to converge to a
on one of these samples, but is only correct exactly at its pixel-perfectresultbyoptimizingthechoiceofthesmooth-
| centre.Iftheviewpointchangesfromoneframetothenext, |               |     |         |       |           |       | ingfactor.    |        |     |        |           |               |
| -------------------------------------------------- | ------------- | --- | ------- | ----- | --------- | ----- | ------------- | ------ | --- | ------ | --------- | ------------- |
| the regular                                        | grid sampling | of  | the new | frame | is likely | to be |               |        |     |        |           |               |
|                                                    |               |     |         |       |           |       | The smoothing | factor | α   | allows | balancing | fast adaption |
completelydifferentthanthepreviousone.Thisfrequently
results in artefacts, especially noticeable for thin geometry onchanginginputparametersagainsttemporalnoise.With
|     |     |     |     |     |     |     | a larger smoothing |     | factor, | the result | depends | more on the |
| --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | ------- | ---------- | ------- | ----------- |
andtheundersampledportionsofthescenecalledtemporal
newshadowresultsfromthecurrentframeandlessonolder
aliasing.
|     |     |     |     |     |     |     | frames and | vice versa. | To  | this end, | the smoothing | factor |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ----------- | --- | --------- | ------------- | ------ |
Thisisespeciallytrueforshadowmaps.Duetoshadow is determined per-pixel according to the confidence of the
map focusing, a change in the viewpoint from one frame shadow lookup. This confidence is defined to be higher if
to the next also changes the regular grid sampling of the thelookupfallsnearthecentreofashadowmaptexel,since
shadowmap.Additionally,therasterizedinformationisnot onlynearthecentreofshadowmaptexels,itisverylikely
accessedintheoriginallightspacewhereitwascreated,but thatthesampleactuallyrepresentsthescenegeometry(see
ineyespace,whichworsenstheseartefacts.Thisfrequently Figure15).Inthispaper,themaximumnormofthecurrent
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2391
| Figure16: | Lightsamplingwith1,2,3and256shadowmaps |     |     |     |     |     |     |     |     |     |     |     |
| --------- | -------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(lefttoright).
|     |     |     |     |     |     | Figure | 17: | Left side: PCSS | 16/16; | Overlapping |     | occlud- |
| --- | --- | --- | --- | --- | --- | ------ | --- | --------------- | ------ | ----------- | --- | ------- |
pixelpandtheshadowmaptexelcentrecisusedtoaccount
|     |     |     |     |     |     | ers | (upper | row) and bands | in big | penumbras | (lower | row) |
| --- | --- | --- | --- | --- | --- | --- | ------ | -------------- | ------ | --------- | ------ | ---- |
forthis
(cid:12) (cid:12)(cid:5) areknownproblematiccasesforsingle-sampleapproaches.
|     | (cid:4) | (cid:4) |     | |,(cid:12) | (cid:12) (cid:5) m, |     |     |     |     |     |     |     |
| --- | ------- | ------- | --- | ---------- | ------------------- | --- | --- | --- | --- | --- | --- | --- |
conf= 1−max |px −cx py −cy ·2 (11) Rightside:softshadowsexploitingTC.
butothernormscouldbeusedaswell.Theparametermde-
| fines how | strict | this confidence |     | is applied. | m<4 results |     |     |     |     |     |     |     |
| --------- | ------ | --------------- | --- | ----------- | ----------- | --- | --- | --- | --- | --- | --- | --- |
in fast updates where most shadow map lookups of the an area light by a point light located at its centre and use
heuristicstoestimatepenumbrae,whichleadstosoftshad-
| current frame | have | a big | weight | and the | resulting shadow |     |     |     |     |     |     |     |
| ------------- | ---- | ----- | ------ | ------- | ---------------- | --- | --- | --- | --- | --- | --- | --- |
m>12 ows that are not physically correct (see Figure 17, left).
| has noisy | edges. |     | results | in accurate | but slow up- |     |     |     |     |     |     |     |
| --------- | ------ | --- | ------- | ----------- | ------------ | --- | --- | --- | --- | --- | --- | --- |
Overlappingoccluderscanleadtounnatural-lookingshadow
dateswheremostlookupsfromthecurrentframehavesmall
|     |     |     |     |     |     | edges, | or  | large penumbrae | can cause | single-sample |     | soft- |
| --- | --- | --- | --- | --- | --- | ------ | --- | --------------- | --------- | ------------- | --- | ----- |
weight.
|     |     |     |     |     |     | shadow | approaches | to either | break | down | or become | very |
| --- | --- | --- | --- | --- | --- | ------ | ---------- | --------- | ----- | ---- | --------- | ---- |
m
| The authors | found | out | that | should | be balanced with | slow. |     |     |     |     |     |     |
| ----------- | ----- | --- | ---- | ------ | ---------------- | ----- | --- | --- | --- | --- | --- | --- |
cameramovement.Whenthecameramovesfast,mcanbe
|               |       |        |        |         |                 |     | One observation | is that | the shadow | samplingcan |     | be ex- |
| ------------- | ----- | ------ | ------ | ------- | --------------- | --- | --------------- | ------- | ---------- | ----------- | --- | ------ |
| small because | noise | at the | shadow | borders | is not noticed. |     |                 |         |            |             |     |        |
Onlyforaslowlymovingcameraorastillimagearehigher tendedovertime.Itis,forexample,possibletochangethe
valuesofmnecessary.Thisismotivatedbythehumanvi- samplingpatternonthesourceineachframe,therebytrading
aliasingartefactswithlessobjectionablerandomnoise.This
| sual system, | which | tends | to integrate | over | motion, thereby |     |              |                 |     |           |       |         |
| ------------ | ----- | ----- | ------------ | ---- | --------------- | --- | ------------ | --------------- | --- | --------- | ----- | ------- |
|              |       |       |              |      |                 | is  | particularly | easy to achieve | for | symmetric | light | sources |
allowingfornoisieredgeswhenstrongmovementispresent.
[ED07b,SEA08].Moregenerally,lightsourceareasampling
Thisconfidencecannowbedirectlyusedintheexponential
smoothingformula(seeSection3.5) canbeformulatedinaniterativemannerbyevaluatingonly
asingleshadowmapperframe[SSMW09].Reformulating
| f t[p]←(conf)s |     | t[p]+(1−conf)f |     |     | (π (p)).     |                   |     |     |     |     |     |     |
| -------------- | --- | -------------- | --- | --- | ------------ | ----------------- | --- | --- | --- | --- | --- | --- |
|                |     |                |     |     | t−1 t−1 (12) | Equation(13)gives |     |     |     |     |     |     |
(cid:13)n(p)
s(p)+(cid:10)(p)
| 5.4.2. Softshadows |     |     |     |     |     |     | ψ(p)= |     |     | (cid:10)(p)= | s i(p), | (14) |
| ------------------ | --- | --- | --- | --- | --- | --- | ----- | --- | --- | ------------ | ------- | ---- |
n(p)+1
| Inreality,mostlightsourcesarearealightsources,andhence |         |      |          |              |          |       |      |                        |     |        | i=1     |         |
| ------------------------------------------------------ | ------- | ---- | -------- | ------------ | -------- | ----- | ---- | ---------------------- | --- | ------ | ------- | ------- |
| most shadows                                           | exhibit | soft | borders. | Light-source | sampling |       | s(p) |                        |     |        |         |         |
|                                                        |         |      |          |              |          | where |      | is the hard shadow-map |     | result | for the | current |
n(p)
[HH97] creates a shadow map for every sample (each on frame and pixel and is the number of shadow maps
a different position on the light source) and calculates the evaluated until the previous frame for this pixel. Note that
average(=softshadow)oftheshadowmaptestresultss ifor now n depends on the current pixel because depending on
eachpixel(seeFigure16).Therefore,thesoftshadowresult howlongthispixelhasbeenvisible,adifferentnumberof
fromnshadowmapsforagivenpixelpcanbecalculated shadow maps may have been evaluated for this pixel. The
n(p)
| by  |     |     |     |     |     | calculation |     | of this formula | is straightforward |     | if  | and |
| --- | --- | --- | --- | --- | --- | ----------- | --- | --------------- | ------------------ | --- | --- | --- |
(cid:10)(p)arestoredinabuffer(anotherinstanceoftheRRC:see
1 (cid:13)n
ψ n(p)= s i(p). Section3.1).Withthisapproach,thesoftshadowimproves
(13)
|     |     |     | n   |     |     | fromframetoframeandconvergestothetruesoftshadow |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ----------------------------------------------- | --- | --- | --- | --- | --- | --- |
i=1
|     |     |     |     |     |     | result | if pixels | stay visible | ‘long | enough’ | (see Figure | 18, |
| --- | --- | --- | --- | --- | --- | ------ | --------- | ------------ | ----- | ------- | ----------- | --- |
Theprimaryproblemhereisthatthenumberofsamples
upperrow).
| (and therefore | shadow | maps) | to  | produce | smooth penum- |     |     |     |     |     |     |     |
| -------------- | ------ | ----- | --- | ------- | ------------- | --- | --- | --- | --- | --- | --- | --- |
braeishuge.Therefore,thisapproachisinefficientinprac- Inpractice,thiscanresultintemporalaliasingforsmall
tice.Typicalmethodsforreal-timeapplicationsapproximate n. Care has to be taken in order to properly manage those
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2392 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
5.5. Globalillumination
Itisamajorgoalofreal-timeresearchtoachieveplausible
(andinthelongrun,physicallycorrect)globalillumination.
|     |     |     |     | In this | section, | we  | present several | techniques | that | explore |
| --- | --- | --- | --- | ------- | -------- | --- | --------------- | ---------- | ---- | ------- |
TCinanattempttoapproximateglobalilluminationeffects
inrealtime.Manytechniquescanbefoundintheexcellent
surveybyDamezetal.[DDM03].Nonetheless,thefocusis
oftenonofflinesolutionsoritisassumedthatknowledgeof
subsequentkeyframesisavailable.Forinteractiverendering,
Figure18: Convergenceafter1,3,7,20and256frames;up- this is not always achievable and specialized solutions are
perrow:samplingofthelightsourceonesampleperframe;
needed.Inthiscontext,itisdifficulttoexploitTConcurrent
lowerrow:softshadowswithTC. GPUs,whichisinthefocusofouroverview.
Theradianceemittedfrompointpintodirectionωcanbe
describedbytherenderingequation[Kaj86,ATS94]
|     |     |     |     | L(p,ω)=L |     | e(p,ω) |     |     |     |     |
| --- | --- | --- | --- | -------- | --- | ------ | --- | --- | --- | --- |
(cid:14)
1
|     |     |     |     |     |     | +   | f r(p,ω(cid:4),ω)L | i(p,ω(cid:4))(n | ·ω(cid:4))dω(cid:4). |      |
| --- | --- | --- | --- | --- | --- | --- | ------------------ | --------------- | -------------------- | ---- |
|     |     |     |     |     |     | π   |                    |                 | p                    | (15) |
(cid:11)
|     |     |     |     | (cid:11)denotesthespaceofallhemisphericaldirections,L |     |                                           |     |     |     | eisthe |
| --- | --- | --- | --- | ----------------------------------------------------- | --- | ----------------------------------------- | --- | --- | --- | ------ |
|     |     |     |     | selfemission,f                                        |     | isthebidirectionalreflectancedistribution |     |     |     |        |
r
|     |     |     |     | function(BRDF),L |     |     | istheincidentlightfromdirectionω(cid:4) |     |     |     |
| --- | --- | --- | --- | ---------------- | --- | --- | --------------------------------------- | --- | --- | --- |
i
andn
pisthesurfacenormal.
|     |     |     |     | Global | illumination |     | algorithms | often | use Monte-Carlo |     |
| --- | --- | --- | --- | ------ | ------------ | --- | ---------- | ----- | --------------- | --- |
samplingtoevaluatethismulti-dimensionalintegralinafea-
sibleway.WecanexploitTCbetweenconsecutiveframes,
e.g.byspreadingtheevaluationoftheintegralovertime.
5.5.1. Screen-spaceambientocclusion
Ambientocclusion[CT81]isacheapbuteffectiveapprox-
|     |     |     |     | imation | of  | global | illumination | which shades | a pixel | with |
| --- | --- | --- | --- | ------- | --- | ------ | ------------ | ------------ | ------- | ---- |
thepercentageofthehemispherethatisblocked.Itcanbe
seenasthediffuseilluminationofthesky[Lan02].Ambient
occlusionofasurfacepointpiscomputedas
(cid:14)
Figure19: StructureofthesoftshadowswithTCalgorithm. (cid:4) (cid:5)
1
|     |     |     |     |     | AO(p,n | )=  | V(p,ω(cid:4)) | n   | ·ω(cid:4) dω(cid:4). | (16) |
| --- | --- | --- | --- | --- | ------ | --- | ------------- | --- | -------------------- | ---- |
|     |     |     |     |     |        | p   | π             | p   |                      |      |
(cid:11)
The(inverse)visibilityfunctionV
wasoriginallydefinedas
cases.Whenapixelbecomesnewlyvisibleandthereforeno abinaryfunctionwhereV(p,ω(cid:4))=1ifthevisibilityinthis
previousinformationisavailableintheRRC,afastsingle-
|     |     |     |     | direction | is  | blocked | by an obstacle, | 0 otherwise. |     | However, |
| --- | --- | --- | --- | --------- | --- | ------- | --------------- | ------------ | --- | -------- |
sampleapproach(PCSSwithafixed4×4kernel)isemployed
|     |     |     |     | other | choices | for | V (e.g. an | exponential | falloff | based on |
| --- | --- | --- | --- | ----- | ------- | --- | ---------- | ----------- | ------- | -------- |
to generate an initial softshadow estimation for this pixel. distance)givevisuallymorepleasing(i.e.smoother)results.
n,
| For all other | the expected | standard error | is calculated |     |     |     |     |     |     |     |
| ------------- | ------------ | -------------- | ------------- | --- | --- | --- | --- | --- | --- | --- |
and if it is above a certain threshold (expected fluctuation Screen-spaceambientocclusion(SSAO)methods[Mit07]
in the soft shadow result in consecutive frames), a depth- sampletheframebufferasadiscretizationofthescenege-
awarespatialfilterisemployedtotakeinformationfromthe ometry. These methods are of particular interest for real-
neighbourhoodintheRRCintoaccount(seeFigure19).This timeapplicationsduetothefactthattheshadingoverhead
approachlargelyavoidstemporalaliasingandcanbenearly ismostlyindependentofscenecomplexity,andseveralvari-
asfastashardshadowmappingifallpixelshavebeenvisible ants of SSAO have been proposed since [FC08, BSD08,
forsometimeandtheexpectedstandarderrorissmallenough SKUT*10].WeassumethatanySSAOmethodcanbewrit-
(seeFigures18and17). tenasanaverageovercontributionsCdependingonaseries
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2393
ofsampless:
i
(cid:13)n
1
SSAOn(p)=
n
C(p,s
i
), (17)
i=1
whereatypicalcontributionfunctionforasingleSSAOsam-
plecanbe
C(p,s)=V(p,s)max(cos(s −p,n ),0). (18)
i i i p
s isanactualsamplepointaroundp,andV(p,s)isnowa
i i
binaryvisibility function thatis resolved by evaluating the
depthtestfors.
i
Reverse reprojection allows us to cache and reuse pre-
viouslycomputedSSAOsamples.ThepropertiesofSSAO
(relatively low-frequency, independence from light-source,
localsupportofthesamplingkernel)arebeneficialforusing
TC, as it was already demonstrated in commercial games
[SW09]. In the following, we discuss the temporal SSAO
(TSSAO) method of Mattausch et al. [MSW10], who fo-
cusonimprovingtheaccuracyandvisualqualityofSSAO
foragivennumberofsamplesperframe,andintroducean
invalidationschemethathandlesmovingobjectswell.
A comparison of conventional SSAO with TSSAO is
showninFigure20.ThenoisyappearanceofacoarseSSAO
solutionthatusesonlyafewsamples(imagea)canbeim-
provedwithascreen-spacespatialdiscontinuityfilter.How-
ever,theresultofthisoperationcanbequiteblurry(imageb).
Aslongasthereisasufficienthistoryforapixel,TSSAOpro-
ducessmoothbutcrispSSAOwithoutdependingonheavy
post-processing(imagec).
Figure 20: SSAO without TC using 32 samples per pixel
Integrationovertime. Inframet,anewcontributionC t with (a) a weak blur, (b) a strong blur (both 23 FPS) and
iscalculatedfromknewSSAOsamples.
(c) temporal SSAO using 8–32 samples (initially 32, 8 in
a converged state) (45 FPS). (d) Reference solution using
1
jt(cid:13)(p)+k
C t(p)=
k
C(p,s
i
), (19) 480samples(2.5FPS).Thescenehas7Mverticesandruns
at62FPSwithoutSSAO.
i=jt(p)+1
wherej t(p)countsthenumberofuniquesamplesthathave
alreadybeenusedinthissolution.Thenewcontributionis
combinedwiththepreviouslycomputedsolution thescreen-spacefiltersupportproportionallytotheconver-
SSAOt(p)= w t−1 (pt−1
w
)S
t−
S
1
A
(
O
p
t
−
−1 (
1
p
)
t
+
−1 )
k
+kC t(p) ,(20) i
h
g m e
ig
n p
h
c r
e
e o
r
v w
w
ed n
e
/
i
b
g
w y
h
m
ts
a m x
t
. a
o
k T
s
i
u
h n
f
e g
fi
r
c
i e t
ie
s c u
n
o l
t
t
l
n s
y
v o e
c
r
o
f g
n
t e
v
h n
e
e c
rg
e fi
e
l a t
d
e w r
fi
i a
l
n
t
r g
e
e
r
, c
s
i a
a
. n e
m
. b
p
a e
l
s
e
s
s
f i u
.
g r n th in e g r
Detectingchanges. Specialattentionmustbepaidtothe
w t(p)=min(w t−1 (pt−1 )+k,w max ). (21) detectionofcachemisses(i.e.pixelswithaninvalidSSAO
Theweightw t−1 representsthenumberofsamplesthathave solution).Acachedvalueofapixelisinvalidifeitheroneof
already been accumulated in the solution, until w max has the following three conditions has occurred: 1) a disocclu-
sionofthecurrentpixel,2)thepixelwaspreviouslyoutside
beenreached.Thesolutionconvergesveryquickly,andthis
theframebufferor3)achangeinthesampleneighbourhood
predefined maximum controls the refresh rate and ensures
ofthepixel.Case1)andcase2)canbehandledlikeconven-
thattheinfluenceofoldercontributionsdecaysovertime.
tionalcachemissesasdescribedpreviouslyinSection3.3.
NotethatforTSSAO,spatialfilteringoftheresulttore- However,itisimportanttoadditionallycheckforcase3),be-
ducenoiseonlyhastobeappliedinregionswherethesolu- causenearbychangesinthegeometrycanaffecttheshading
tionhasnotsufficientlyconverged.Thisisdonebyshrinking ofthecurrentpixel.
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2394 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
|     |     |     |     |     |     | Figure22: | Movingdragonmodelusingnoinvalidation(left, |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --------- | ------------------------------------------ | --- | --- | --- | --- | --- |
causingsevereartefactsintheshadow),andusinganinval-
idationfactorsettoapropervalue(right,noartefacts).
S
|     |     |     |     |     |     | The invalidation | factor       |                               | is a parameter |          | which controls |        |
| --- | --- | --- | --- | --- | --- | ---------------- | ------------ | ----------------------------- | -------------- | -------- | -------------- | ------ |
|     |     |     |     |     |     | the smoothness   | of           | the invalidation.             |                | The      | overall        | confi- |
|     |     |     |     |     |     | dence conf(p)    | in the       | previous                      | SSAO           | solution | is given       | by     |
|     |     |     |     |     |     | min(conf(s       | ),...,conf(s | )).Thisvalueisusedtoattenuate |                |          |                |        |
0 k
|     |     |     |     |     |     | theweightw | giventothesolutionofthepreviousframein |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ---------- | -------------------------------------- | --- | --- | --- | --- | --- |
t
| Figure21: | Thedistanceofptosamplepoints |     |     |     | 2 inthecurrent |     |     |     |     |     |     |     |
| --------- | ---------------------------- | --- | --- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- |
Equation(21).Figure22showstheeffectoftheinvalidation
| framedifferssignificantlyfromthedistanceofp |     |     |     |     | t−1 tos |            |              |        |     |         |               |     |
| ------------------------------------------- | --- | --- | --- | --- | ------- | ---------- | ------------ | ------ | --- | ------- | ------------- | --- |
|                                             |     |     |     |     | 2t−1    | and smooth | invalidation | factor | on  | a scene | with a moving |     |
inthepreviousframe;hence,itcanbesavelyassumedthata
object.
localchangeofgeometryoccurred,whichaffectstheshading
ofp.
5.5.2. Instantradiosity
Instantradiosity[Kel97]isahardware-friendlyglobalillu-
| The | authors | use sampling | to check | the | neighbourhood |     |     |     |     |     |     |     |
| --- | ------- | ------------ | -------- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- |
minationmethodthatcomputesso-calledvirtualpointlights
| of a | pixel for | changes | in the AO | value. In | practice, this |     |     |     |     |     |     |     |
| ---- | --------- | ------- | --------- | --------- | -------------- | --- | --- | --- | --- | --- | --- | --- |
(VPLs)alongtheintersectionsofalightpathwithasurface
| neighbourhood |           | test does      | not introduce | additional | lookups, |          |                   |     |                     |     |              |     |
| ------------- | --------- | -------------- | ------------- | ---------- | -------- | -------- | ----------------- | --- | ------------------- | --- | ------------ | --- |
|               |           |                |               |            | C        | and uses | them for indirect |     | scene illumination. |     | The visibil- |     |
| as the        | available | set of samples | used          | to compute | t(p) can |          |                   |     |                     |     |              |     |
ityisresolvedbycomputinganindividualshadowmapfor
bereused.Itisanimportantobservationthatacontribution
|     |     |     |     |     |     | each VPL. | The shadow-map |     | computation |     | is also the | main |
| --- | --- | --- | --- | --- | --- | --------- | -------------- | --- | ----------- | --- | ----------- | ---- |
C(p,s)onlyvariesiftheconfigurationofasampleposition
|     | i   |     |     |     |     | bottleneckofthealgorithm,asitrequiressamplingthescene |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ----------------------------------------------------- | --- | --- | --- | --- | --- | --- |
s relativetopchanges(e.g.theAOonarotatingobjectonly
| i   |     |     |     |     |     | many times | for a reasonable |     | number | of VPLs. | This | draw- |
| --- | --- | --- | --- | --- | --- | ---------- | ---------------- | --- | ------ | -------- | ---- | ----- |
changesinthevicinityofotherobjects).Hence,asillustrated
backpreventsreal-timeframeratesfortheoriginalversion
inFigure21,thealgorithmusesthedistancedifferences
ofthisalgorithm.Inthefollowing,wewilldemonstratehow
δ(s i)=||s −p|−|s −p || t o u s e o b j ec t - l e v e l a n d pi x e l -l e v el T C to i m p ro v e t h e p e r f o r -
|     |     | i   | it−1 | t−1 | (22) |                 |                   |               |            |             |                 |             |
| --- | --- | --- | ---- | --- | ---- | --------------- | ----------------- | ------------- | ---------- | ----------- | --------------- | ----------- |
|     |     |     |      |     |      | m a n c e a n d | v i s u a l q u a | l ity o f t h | i s im p o | rta nt g lo | b a l ill u m i | n a t i o n |
algorithm.
| as a    | measure | of change. | The change | in the             | surface angle |                              |     |     |     |                      |     |     |
| ------- | ------- | ---------- | ---------- | ------------------ | ------------- | ---------------------------- | --- | --- | --- | -------------------- | --- | --- |
| between | s and   | p could    | have been  | used additionally, | but it        |                              |     |     |     |                      |     |     |
|         | i       |            |            |                    |               | Incrementalinstantradiosity. |     |     |     | ByreusingVPLvisibil- |     |     |
wouldhavecausedanadditionaloverhead.Itissufficientto
|     |     |     |     |     |     | ity over time, | Laine | et al. | [LSK*07] | proposed | a method |     |
| --- | --- | --- | --- | --- | --- | -------------- | ----- | ------ | -------- | -------- | -------- | --- |
usethosesamplesthatlieinfrontofthetangentplaneofp
thatexploitsobject-levelTCtoreachreal-timeframerates.
fortheneighbourhoodtest,sinceonlythosesamplesactually
Forthesakeofperformance,thisalgorithmonlycomputes
modifytheshading.
first-bounceindirectillumination,whichissufficientinmost
Smooth invalidation. Consider, for example, a slowly cases.Evenso,hundredsofshadowmapsareneededforcon-
deformingsurface,wheretheSSAOwillalsochangeslowly. vincingglobalillumination.Inordertokeepthenumberof
VPLcomputationsperframefeasibleforreal-timepurposes,
Insuchacase,itisnotnecessarytofullydiscardtheprevious
thisalgorithmsreusesthevalidVPLsfromthepreviousframe
| solution. | Instead, | the authors | introduce | a new | continuous |     |     |     |     |     |     |     |
| --------- | -------- | ----------- | --------- | ----- | ---------- | --- | --- | --- | --- | --- | --- | --- |
definitionofinvalidationthattakesameasureofchangeinto andrecomputesonlyasmallbudgetofinvalidshadowmaps
account.Thismeasureofchangeisgivenbyδ(s)atvalidation inaframe.AVPLstaysvalidifitiswithinthelightfrustum
i
samplepositions,asdefinedinEquation(22).Inparticular, and is not occluded from the light source (which is tested
i
witharaycaster).ThealgorithmisvisualizedinFigure23.
| thealgorithmcomputesaconfidencevalueconf(s)between |     |     |     |     | i   |     |     |     |     |     |     |     |
| -------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
0and1.ItexpressesthedegreetowhichthepreviousSSAO
Themaintaskofthisalgorithmistoincrementallymain-
solutionisstillvalid:
|     |     |            |     |     |     | tain a good      | distribution | of              | the VPLs | during        | consecutive |     |
| --- | --- | ---------- | --- | --- | --- | ---------------- | ------------ | --------------- | -------- | ------------- | ----------- | --- |
|     |     |            |     | 1   |     | frames. Assuming | a            | 180◦ spotlight, |          | the algorithm | uses        | the |
|     |     | conf(s)=1− |     | .   |     |                  |              |                 |          |               |             |     |
i 1+Sδ(s) (23) fact that a cosine-weighted distribution on a hemisphere
i
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2395
|     |     |     |     | rithm. | This | method | allows | hundreds | of shadow | map-based |     |
| --- | --- | --- | --- | ------ | ---- | ------ | ------ | -------- | --------- | --------- | --- |
visibilityqueriesperframeinatleastinteractivetime.
However,evensuchalargenumberofqueriesisinsuffi-
cienttoavoidtypicalundersamplingartefacts,e.g.resulting
inflickeringbetweenframesiftheVPLsarerecomputed.In
ordertoimprovethevisualqualityandreducetheseartefacts,
Figure 23: (Left) Instant radiosity shoots paths from the itisstraightforwardtocombinetheimperfectshadowmap
lightsource,andcreatesVPLsattheintersectionwithgeom- approachwithtemporalreprojection.
etry.(Middle)Usingshadowmaps,thevisibilityofeachVPL
|           |                             |          |             |      | Recently, | the undersampling |         | issues             | were | addressed | to  |
| --------- | --------------------------- | -------- | ----------- | ---- | --------- | ----------------- | ------- | ------------------ | ---- | --------- | --- |
| and their | contribution to the current | image is | determined. |      |           |                   |         |                    |      |           |     |
|           |                             |          |             | some | extent    | by                | relying | on a view-adaptive |      | solution  |     |
(Right)TC:Whentheviewpointorlightsourcemoves,one
|     |     |     |     | [REH*11]. |     | The idea | is to | update a | part of | the point-based |     |
| --- | --- | --- | --- | --------- | --- | -------- | ----- | -------- | ------- | --------------- | --- |
oftheVPLsbecomesinvisiblefromthelightsource,andall
scenerepresentationforeachframe,therebyensuringmore
theothersarereused.ImagecourtesyofSamuliLaine.
precisionwheresurfacesvisibletotheobserverareaffected.
|     |     |     |     | Also,     | the | VPL selection |         | and placement | is          | optimized | by   |
| --- | --- | --- | --- | --------- | --- | ------------- | ------- | ------------- | ----------- | --------- | ---- |
|     |     |     |     | proposing |     | a novel       | scheme. | By selecting  | appropriate |           | VPLs |
fromalargesetofpotentialVPLsdependingontheiresti-
matedimpactonthevisiblescenefromtheobserver,much
|     |     |     |     | higher | fidelity | is achieved. |     | Further, | by employing | a   | novel |
| --- | --- | --- | --- | ------ | -------- | ------------ | --- | -------- | ------------ | --- | ----- |
VPL-placementschemefordynamiclightsources,theytend
tomoveinamorecontinuouswayovercontinuoussurfaces.
Therefore,thetemporalconsistencyofindirectillumination
issignificantlyimproved.
ThemainproblemofusingTCforglobalilluminationis
theglobalnatureofchangesofthelightingconditionsandthe
Figure24: Anuniformdistributionontheunitdisccorre- sceneconfiguration—sometrade-offbetweensmoothingand
sponds to a cosine-weighted distribution on a hemisphere. correctnessisinevitableandasatisfactorygeneralsolution
The VPL management aims to keep the uniformity of the ishardtofind.Knechtetal.[KTM*10]chosetouseacon-
VPLsontheunitdiscwhilerecomputingabudgetofVPLs fidencevalueinsteadofabinarythresholdforinvalidation.
perframe.ImagecourtesyofSamuliLaine. Inparticular,theconfidenceinreusingaprevioussolutionis
guidedbytheamountofchangeofapixelbetweenthepre-
viousandcurrentframe.Tothisend,theyintroduceacouple
ofparameters:
| corresponds | to a uniform distribution | on a disc | (as shown |     |     |     |     |     |     |     |     |
| ----------- | ------------------------- | --------- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
inFigure24).InordertomanagetheVPLdistributiononthe
|                                                       |     |     |     |     | (cid:5) | =||(x   | t −x t−1 | ;y t −y t−1 | ;d t −d | t−1 )w ||, |     |
| ----------------------------------------------------- | --- | --- | --- | --- | ------- | ------- | -------- | ----------- | ------- | ---------- | --- |
| unitdisc,thealgorithmcreatesa2DDelaunaytriangulation. |     |     |     |     | pos     |         |          |             |         | p          |     |
|                                                       |     |     |     |     | (cid:5) | =(1−n·n |          | )w ,        |         |            |     |
To choose the best position for new VPLs, the algorithm norm prev n
|     |     |     |     |     | (cid:5) | =saturate(||I |     | −I ||3)w | ,   |     |     |
| --- | --- | --- | --- | --- | ------- | ------------- | --- | -------- | --- | --- | --- |
minimizesdispersion,whichiscomputedastheradiusofthe ill t t−1 i
|                                                     |     |     |     |     | conf | =saturate(1−max((cid:5) |     |     | ;(cid:5) ;(cid:5) | ill))c . |      |
| --------------------------------------------------- | --- | --- | --- | --- | ---- | ----------------------- | --- | --- | ----------------- | -------- | ---- |
|                                                     |     |     |     |     |      |                         |     | pos | norm              | B        |      |
| largestemptycirclethatcontainsnosamplepoints.Incase |     |     |     |     |      |                         |     |     |                   |          | (24) |
ofomni-directionallightsources,thealgorithmoperateson
|     |     |     |     | Thethree(cid:5) |     | termscomputethreedistancevaluesofscreen- |     |     |     |     |     |
| --- | --- | --- | --- | --------------- | --- | ---------------------------------------- | --- | --- | --- | --- | --- |
theunitsphereinsteadoftheunitdisc.
|     |     |     |     | space                    | position | and | depth, | normal and | illumination |     | value, |
| --- | --- | --- | --- | ------------------------ | -------- | --- | ------ | ---------- | ------------ | --- | ------ |
|     |     |     |     | respectively.Theweightsw |          |     |        | ,w andw    |              |     |        |
Notethatthealgorithmcaptureschangesinthescenewith p n i arehighlyscene-
acertainlatency,andshadowscastfromdynamicobjectsare dependentandrequirefine-tuningbytheuser.Thefinalcon-
notsupported.Theauthorsreportaspeedupfrom1.4to6.8 fidenceiscomputedasthemaximumofthesemeasuresmul-
fordifferentscenesandresolutions.Intheirtests,theyfixed tipliedbysomebaseconfidencec B,andisthenusedasthe
thenumberofVPLsto256andtherecomputationbudgetto weight of a standard exponential smoothing operation (see
| 4–8VPLs. |     |     |     | Section3.5). |     |     |     |     |     |     |     |
| -------- | --- | --- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- |
Imperfectshadowmaps. Basedontheobservationthat AscanbeseeninFigure25,TCimprovesthequalityand
coarsevisibilityissufficientforlow-frequencyglobalillumi- reduces the noise caused by the undersampling. The qual-
nation,Ritscheletal.[RGK*08]significantlyacceleratethe ity improvement is most visible during animations, where
VPLgenerationforinstantradiosity.Theyuseapoint-based distractingflickeringartefactsduetovaryingVPLpositions
scene representation and distribute these points among the canbeavoidedusingTC.Duetothelow-frequencynature
VPLstogenerateso-calledimperfectshadowmaps.While ofindirectillumination,theartefactscausedbymovinglight
each shadow map is sampled with only a coarse subset of sourcesandanimatedobjectsarenotverydistractinginthe
scene points, holes can be closed with a pull–push algo- generalcase(theyaresimilartomotionblur).
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2396 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
effects,Herzogetal.proposedtoexaminethetemporalgra-
dientofthepreviouslyconstructedframeandtheonlyspa-
tiallyupsampledcurrentframe.Ifthegradientislow,more
|     |     |     |     |     |     | confidence | is given | to temporal | weights, |     | if not, the algo- |
| --- | --- | --- | --- | --- | --- | ---------- | -------- | ----------- | -------- | --- | ----------------- |
rithmfavoursspatialupsamplingtechniquestoproducethe
finalhigh-qualityversionofthecurrentframe.Theintuition
issimple.Ifaregionofanimagechangedlittleovertime,
|     |     |     |     |     |     | it is useful | to exploit | more | samples | from | previous frames, |
| --- | --- | --- | --- | --- | --- | ------------ | ---------- | ---- | ------- | ---- | ---------------- |
whereasifstrongchangesoccurred,oldervaluesshouldbe
Figure25: Imperfectshadowmapsstillshowsomeartefacts considered unreliable. In order to make this solution more
with256VPLs,whichcanbesmoothedoutusingTC.Image robust to outliers, a temporal smoothing is applied to the
| courtesyofMartinKnecht. |     |     |     |     |     | gradient.                        |     |     |     |                 |     |
| ----------------------- | --- | --- | --- | --- | --- | -------------------------------- | --- | --- | --- | --------------- | --- |
|                         |     |     |     |     |     | Eachlow-resolutionshadingframefl |     |     |     | isproducedusing |     |
t−q
interleavedsampling,meaningthatthecameraischangedto
5.6. Spatio-temporalupsampling
ensurethatwhenputtingalllow-resolutionimagestogether,
In addition to TC, also spatial coherence may exist within onecanactuallyproduceacompletehigh-resolutionrender-
shading signals (e.g. low-frequency diffuse shading). Her- ingwithoutartefacts.Inpractice,thetemporalfadeoutmakes
zog et al. [HEMS10] proposed a spatio-temporal upsam- itimpossibletoensureaperfectmatch,butthequalityisstill
pling technique that exploits temporal and spatial redun- higherthanforspatialortemporalupsamplingalone.
| dancy. Strong | temporal | changes        | (e.g. moving    | lights)      | are    |                         |     |     |     |     |     |
| ------------- | -------- | -------------- | --------------- | ------------ | ------ | ----------------------- | --- | --- | --- | --- | --- |
| handled with  | spatial  | upsampling,    | while coherency |              | is ex- |                         |     |     |     |     |     |
|               |          |                |                 |              |        | 5.7. Frameinterpolation |     |     |     |     |     |
| ploited to    | ensure   | a high-quality | convergence     | via temporal |        |                         |     |     |     |     |     |
upsampling.Suchspatio-temporalfilteringisoftenapplied
Frameinterpolationiswidelyappliedinvideoencodingand
forvideorestoration[Tek95,BM05]andcanalsobeusedto
usestemporalredundancytoallowforabettercompression
suppressaliasingartefacts[Shi95].
|     |     |     |     |     |     | behaviour. | We will | investigate | compression |     | and streaming |
| --- | --- | --- | --- | --- | --- | ---------- | ------- | ----------- | ----------- | --- | ------------- |
brieflyinSection5.10.Here,weanalyzeasecondreasonto
Thebasicapproachofspatio-temporalupsamplingfollows
employframeinterpolationstrategies:hold-typeblur.
ajoint-orcross-bilateralupsampling[TM98,SB95,ED04,
PSA*04,KCLU07,YSL08]scheme:
Nowadays,hold-typedisplays,suchasLCDscreens,show
|     |     |     | (cid:15) (cid:15) |     |     |     |     |     |     |     |     |
| --- | --- | --- | ----------------- | --- | --- | --- | --- | --- | --- | --- | --- |
T a n im a g e o v e r a l o n g e r p e ri o d o f t im e i n s te ad o f fl a s h i n g it o n
| f t(p)= |     | (cid:15) 1 |     |     |     |     |     |     |     |     |     |
| ------- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ws wtwf q=0 j∈N{pq} th e sc re e n . T h e r e s u l ti n g p e r ce p t u al e f fe c ts ar e v e r y i n t er es t -
|     | ws(pq | ,j)wt(pq | ,j)wf(q) | f l (jˆ), |     |     |     |     |     |     |     |
| --- | ----- | -------- | -------- | --------- | --- | --- | --- | --- | --- | --- | --- |
t −q
|     |     |     |     |     | (25) | ing.Infact,movingcontentisperceivedblurredbecausethe |     |     |     |     |     |
| --- | --- | --- | --- | --- | ---- | ---------------------------------------------------- | --- | --- | --- | --- | --- |
eyetracksthecontentoverthescreen.Duringtheeyemotion,
whereN describesaspatialneighbourhoodaroundapixel
theimagecontentstayspartlyconstant(duetoaninsufficient
andqisanindexthatindicatestheframesovertime.Hence,
framerate),whichleadstoanintegrationoftheimageonthe
the double summation takes space and time into account. retina(notunlikemotionblur)[KV04].Foralongtime,alot
Weightwscomputestheworld-spacedistanceandsimilarity
oftheblurperceptionwaswronglyattributedtothedisplay’s
ofsamplesbasedonsurfacepropertiessuchasnormalsorma-
responsetime,butPanetal.[PFD05]showedthatonly30%
| terialindices.Weightwt       |     | isabinaryocclusiontest,checking |                            |     |     |                  |            |            |              |     |                  |
| ---------------------------- | --- | ------------------------------- | -------------------------- | --- | --- | ---------------- | ---------- | ---------- | ------------ | --- | ---------------- |
|                              |     |                                 |                            |     |     | of the perceived |            | blur are a | consequence  | of  | it. The remain-  |
| whetherthereprojectedpixelpq |     |                                 | =π t−q(p)isactuallyvisible |     |     |                  |            |            |              |     |                  |
|                              |     |                                 |                            |     |     | ing 70%          | are mostly | a result   | of hold-type |     | blur. Especially |
inthecorrespondingframe.Weightwf
describesatemporal for low frame rates, this effect can have dramatic conse-
fadeoutthatreducestheinfluenceofolderpixels.Theterm
|            |            |               |               |     |      | quences | and reduce | the image | quality | drastically | [Jan01], |
| ---------- | ---------- | ------------- | ------------- | --- | ---- | ------- | ---------- | --------- | ------- | ----------- | -------- |
| (cid:15) 1 | normalizes | the weighting | coefficients. | The | term |         |            |           |         |             |          |
wswtwf but even reaction times decrease and task performance is
f l
t −q are low-resolution frames that were created using an reduced[DER*10b].
| interleaved | pixel | refresh at | time t−q and | consequently, | jˆ  |     |     |     |     |     |     |
| ----------- | ----- | ---------- | ------------ | ------------- | --- | --- | --- | --- | --- | --- | --- |
ModernTVstrytooptimizeimagequalitybyemploying
istheindexofthenearestpixelinthelow-resolutionimage
that corresponds to pixel j. While, in theory, it seems that interpolationschemes[FPD08].Whileanaccurateinterpo-
lationandmatchingofcontentovertimecanbecomevery
manypreviousframeshavetobekeptinmemory,choosing
|     |     |     |     |     |     | difficult for | a TV | set because | optical | flow | is challenging |
| --- | --- | --- | --- | --- | --- | ------------- | ---- | ----------- | ------- | ---- | -------------- |
exponentialweightsallowsforanaccumulationinasingle
tocomputerobustly,arenderingcontextoffersmanyadvan-
historybuffer[HEMS10].
tagessincetheproblemisactuallymuchsimpler.Itispossible
Nonetheless, when involving samples from previous toderiveaccuratevelocityandgeometricinformationfrom
frames, it is important to detect which pixel shading val- a scene by simply rendering it into a buffer. Thereby, one
uesarestillusefulforthecurrentframe.Forafastmoving can avoid approximate image-based estimates. TV sets are
light,forexample,shadowsmightchangetheirlocationand stillsuccessfulinmanycasesbecause,athighframerates,
easilypolluteatemporalintegration.Inordertocapturethese the precision of our perception is reduced. Consequently,
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2397
intermediateimagesdonothavetoexhibitthesamequality
askeyframes.
Didyketal.[DER*10b]introducedamethodthatbuilds
upontheobservationthatintermediateframescanbeoflower
qualityandexploittheeffectalgorithmically.Theirapproach
producesahighframeratesequencethatisthendirectlyfed
unaltered to a high-refresh LCD screen. They rely on the
keyobservationthatthehumanvisualsystemspreadshigh
frequenciesofoneframeoversucceedingblurredframesif
asufficientlyhighframerateisreached[TV05].Therefore,
theycanhidepotentialartefactsinwarpedframes.Morepre-
Figure26: Examplesofstylizingaframefromarendered
cisely, they extrapolate a given image and blur all parts of
3Danimationofatankscene(left)anda3Danimationofa
the warped image that might potentially exhibit a reduced
lizardwithastillphotographinthebackground(right).
imagequality.Thefrequenciesthatarelostbytheblurring
processintheextrapolatedframescanbecompensatedfor
intheunwarpedoriginalframe.Intheaffectedregions,the
amplitudeofthehighfrequenciesisincreasedaccordingto turerenderedframeonlyintroducesasmallamountoflag,
the blur that is applied to the successive frames. Because and their user studies show that the effect of this lag was
artefacts are hidden by the blur, a very cost-effective grid minor.Themethodyieldssubstantialperformanceimprove-
warpingstrategycanbeused.Thisgridisdeformedbyve- mentstobothvertex-boundandpixel-boundscenes,aswell
locityvectorsthataredirectlyextractedfromthescene,and asmulti-passrenderingtechniques,suchasdeferredshading
asnappingprocessensuresthatthemaindiscontinuitiesare andmotionblur.
respected.Thetechniqueissuccessfulenoughtoenablethe
additionoftwointermediateframes.Inotherwords,a40Hz
5.8. Non-photorealisticrendering
sequence can be transformed into a 120 Hz output that is
almostindistinguishablefromanactuallyrendered120Hz
Real-time reprojection has also been used by a non-
sequence,whichwasconfirmedbyauserstudy.
photorealistic rendering (NPR) system that converts ani-
Andreev [And10] also proposed a temporal upsampling matedscenestoartisticbrush-strokerenderingsofdifferent
scheme,butmakesuseofanapproximateimage-basedwarp- styles[LSF10].ComputinganewsetofNPRstrokesfrom
ing strategy. He targets only a single in-between frame to scratchineachframeofananimationsequenceresultsinsig-
successfullytransform30Hzsequencesto60Hz.Theidea nificantflickeringartefacts.Instead,thealgorithmmaintains
istorelyagainonaframeextrapolation,buttofurthersep- TCbytreatingbrushstrokesasparticlesandadvectingthe
arate static and dynamic content. Static elements are usu- vastmajorityofthemaccordingtothescenemotion.
allywellhandledbywarpingstrategies,butdynamicobjects
Inordertoadvectbrushstrokes,thealgorithmgeneratesa
canhide—andwhenwarped,unveil—importantpartsofthe
bufferthatstoresper-pixelforwardmotionvectorsforthean-
scene. Consequently, holes can appear in the extrapolated
imatedscene.Thisbuffercanbeefficientlycomputedonthe
frames.Andreevproposestocopystaticpixelpatchesfrom
GPUbyusingreprojectiontocalculatetheforwardmotion
theneighbourhoodtofilluptheseholes.Thedynamiccontent vectorfromframet−1toframet inthevertexshader.The
isthenaddedontopofthefinalshot.Thealgorithmisuseful
motionvectorisinterpolatedbythehardwareandprovided
andwell-adaptedforcurrentgameconsoles(XBox,PS3).It
asinputtothepixelshader.Muchliketraditionalreprojec-
findsapplicationinseveralshippinggametitles,whichshows
tion, the pixel shader homogenizes the motion vector and
itspracticalrelevance.Andreevalsoexploresasolutionthat
thenoutputstheresulttotherendertargetintheclipspace
interpolates between two frames for more accurate results. offramet−1.Finally,eachbrushstrokeparticleusesthis
Hereportsthatitrequiresmorecomputationalresourcesand
motion vector buffer to forward reproject its position from
addsanextraframeoflatency,whichisunsuitabletotheir frame t−1 to frame t. Figure 26 shows examples of syn-
games.
theticscenesrenderedwiththissystem.
Concurrent with Andreev’s talk [And10], Yang et al.
Recently,solutionsalsofocusedondifferentwaysofat-
[YTS*11] introduced a method that interpolates a pair of
tachingbrushstrokestoextractedfeaturecurves.SLAMtex-
consecutiverenderedframes.Theyproposedanewimage-
tures [BCGF10] (self-similar line artmaps) are a means to
basedreprojectionstrategyasdescribedinSection3.2,which
produceamulti-resolutionrepresentationofastylizedline
isusedtoretrievetheinformationfrombothrenderedframes
pattern.Basically,thestylizedpatternisself-similaronsev-
foreachinterpolatedframe.Themethodavoidsrasterizing
eralresolutionlevels.Thispropertyisassuredbyperforming
scenegeometryaltogetherattheseintermediateframesand
a suitable texture synthesis algorithm that derives smooth
is very efficient. With their implementation, using the fu-
transitionsfromasimplepatterntoamoredetailed higher
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2398 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
resolutionversion.Duringrendering,theappropriatedetail
levelcanbechosenfromtheSLAMrepresentation.Unfor-
| tunately, when | moving | elements | over | time, these | strokes, |     |     |     |     |     |
| -------------- | ------ | -------- | ---- | ----------- | -------- | --- | --- | --- | --- | --- |
whilemaintainingacoherentlook,mayslideoverthesur-
| face as the | extracted | feature | lines on | the mesh, | and hence, |     |     |     |     |     |
| ----------- | --------- | ------- | -------- | --------- | ---------- | --- | --- | --- | --- | --- |
theirparametrizationmaychange.Theapproachsuggeststo
| keep similar | texture | coordinates | over | time by | reprojecting |     |     |     |     |     |
| ------------ | ------- | ----------- | ---- | ------- | ------------ | --- | --- | --- | --- | --- |
theparametrizationwhencomputingthenextframe.
| Kalnins                  | et al. [KMM*02, |            | KDMF03]       | avoid         | the use of  |     |     |     |     |     |
| ------------------------ | --------------- | ---------- | ------------- | ------------- | ----------- | --- | --- | --- | --- | --- |
| specialized              | line patterns   | and        | instead       | proposed      | to optimize |     |     |     |     |     |
| the line parametrization |                 | itself.    | They          | also focus    | on tempo-   |     |     |     |     |     |
| rally consistent         | textured        | lines      | and aim       | at minimizing | the         |     |     |     |     |     |
| mentioned                | sliding or      | stretching | that          | would occur   | for naive   |     |     |     |     |     |
| parametrizations.        | By              | tracking   | particle-like | curve         | elements    |     |     |     |     |     |
on the surface, they enable a certain continuity of the ren- Figure 27: LOD interpolation combines two buffers con-
tainingthediscreteLODstocreatesmoothLODtransitions.
| dering. Nonetheless, |     | topological | changes | of the | extracted |           |                |          |              |          |
| -------------------- | --- | ----------- | ------- | ------ | --------- | --------- | -------------- | -------- | ------------ | -------- |
|                      |     |             |         |        |           | First and | second column: | buffers; | last column: | combina- |
featurecurvescannotbeeasilyparametrizedastheyarein-
|     |     |     |     |     |     | tion. The | top row shows | the two | LODs in | red and blue, |
| --- | --- | --- | --- | --- | --- | --------- | ------------- | ------- | ------- | ------------- |
herentlyinconsistent.Byanalyzingadefinedanimationse-
respectively.
quence,onecandetecttopologicaleventsusingaspace-time
contoursurface[BFP*11].Bycouplingcutsandmerges,dis-
continuitiesarereducedandthefinalparametrizationisopti-
5.9.1. DiscreteLODblending
mizedviaaleast-squaresfitthatoptimizestextureslidingand
stretch. A more practical solution to this problem proposed by
[GW06]istoincludeatransitionphaseduringwhichboth
| Kass and | Pesare | [KP11] | introduced | a method | for gen- |          |                   |         |          |             |
| -------- | ------ | ------ | ---------- | -------- | -------- | -------- | ----------------- | ------- | -------- | ----------- |
|          |        |        |            |          |          | LODs are | rendered and then | blended | into the | final image |
eratingcoherentnoiseforNPRapplications.Theirmethod [GW06].Apartfromotherproblems,thisapproachrequires
achievestheillusionofrandomvariationinthenoisefrom
thatthegeometry(andtheshaders)ofbothLODshavetobe
anygivenviewpointinananimationsequencewhileremain-
renderedinthistransitionphase,therebygeneratingahigher
ingtemporallycoherent.Topreservecoherence,theyemploy
renderingcostthanthehigherqualitylevelalonewouldin-
arecursivefilterandhandledisoclusionbycomparingrepro-
cur.Tocircumventthis,ScherzerandWimmer[SW08]in-
jecteddepthvaluesmuchlikeinreversereprojectioncaching. troduced a solution that performs LOD interpolation (see
ManyothertechniquestakeadvantageofTCforstylized Figure 27). The idea is that by using TC, the two LODs
animations.Foradetailedtreatmentofallthesetechniques, requiredduringanLODtransitioncanberenderedinsubse-
quentframes.Twoseparaterenderpassesareusedtoachieve
refertotherecentsurveybyBe´rnardetal.[BBT11].
thetransitionphasebetweenadjacentLODrepresentations:
Pass1rendersthesceneintoanoff-screenbuffer(calledLOD
buffer).Forobjectsintransition,oneofthetwoLODrepre-
5.9. Level-of-detail
sentationsisusedandonlyacertainamountofitsfragments
The idea behind discrete level-of-detail (LOD) techniques arerendered(seeFigure28),dependingonwhereinthetran-
is to use a set of representations with differing complexi- sition(i.e.howvisible)thisobjectcurrentlyis.Thisislater
ties(levelsofdetail)foronemodelandselectthemostap- repeatedinthenextframeusingtheotherLODrepresenta-
propriaterepresentationforrenderingatruntime[LRC*02]. tionandrenderingintoasecondLODbuffer.Thesecondpass
Complexitycan,forinstance,varyintheemployedmaterials
combinesthesetwoLODbuffers(onefromthecurrentand
orshadersorintheamountoftrianglesused.Duetomemory one from the previous frame) to create the desired smooth
| constraintsandtheeffortinvolvedinthecreationprocessof |     |     |     |     |     | transitioneffect. |     |     |     |     |
| ----------------------------------------------------- | --- | --- | --- | --- | --- | ----------------- | --- | --- | --- | --- |
LODs,usually,onlyasmallnumberisemployed,whichcan
resultinnoticeablepoppingartefactswhenswitchingfrom 5.9.2. LODcuts
onerepresentationtoanother.Atheoreticalsolutionwouldbe
toswitchonlywhentherespectivepixeloutputoftworepre- Anotherparticularrepresentationistheuseofscenehierar-
|     |     |     |     |     |     | chies for | rendering purposes. | The | key idea | is to represent |
| --- | --- | --- | --- | --- | --- | --------- | ------------------- | --- | -------- | --------------- |
sentationsisindistinguishable.Thisso-calledlateswitching
|     |     |     |     |     |     | a scene in | form of a tree | where | each node | stores an ap- |
| --- | --- | --- | --- | --- | --- | ---------- | -------------- | ----- | --------- | ------------- |
haspracticalproblems.First,itishardtoguaranteeequality
inpixeloutputforagivenviewscenarioandlightingwithout proximatescenerepresentationforthegivenprecisionlevel
renderingbothrepresentationsfirst,which,ofcourse,defeats corresponding to a level in the tree. While one could start
thepurpose.Second,theideaofswitchingaslateaspossible the searchforan appropriate cut(selectionofnodes)fora
|     |     |     |     |     |     | given view | from the top | of the tree, | this solution | is often |
| --- | --- | --- | --- | --- | --- | ---------- | ------------ | ------------ | ------------- | -------- |
counteractsthepotentialgainofemployingLODsinthefirst
|     |     |     |     |     |     | wasteful. | A cut from one | frame to | the next | rarely changes |
| --- | --- | --- | --- | --- | --- | --------- | -------------- | -------- | -------- | -------------- |
place.Inpractice,switchingisdoneassoonas‘acceptable’.
|     |     |     |     |     |     |     |     |     | (cid:2)c 2012TheAuthors |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------------------- | --- |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2399
Usually,datastructuresareusedtodecomposetheoriginal
datasetinahierarchicalmanner.Theideaistousestructures
|     |     |     |     |     |     | that can be | selectively |     | refined. Once | the | right | refinement |
| --- | --- | --- | --- | --- | --- | ----------- | ----------- | --- | ------------- | --- | ----- | ---------- |
scaleisestablishedforaview,onlylocalmodificationsare
|     |     |     |     |     |     | applied to  | update    | the structure | for           | the next | frame, | as seen    |
| --- | --- | --- | --- | --- | --- | ----------- | --------- | ------------- | ------------- | -------- | ------ | ---------- |
|     |     |     |     |     |     | previously  | for LODs. | This          | lazy          | update   | scheme | implicitly |
|     |     |     |     |     |     | exploits TC | because   | the           | modifications | from     | one    | frame to   |
thenextcanoftenbedrasticallylimited.Insomecases,even
movementpredictioncanprovesuccessful[LKR*96].Inany
|     |     |     |     |     |     | case, deriving | an  | entirely | new refinement |     | would | lead to a |
| --- | --- | --- | --- | --- | --- | -------------- | --- | -------- | -------------- | --- | ----- | --------- |
hugeperformanceoverhead.
Thesehierarchicaldatastructuresarefurtherdesignedin
aflexibleway,inthesensethattheactualgeometricinfor-
|     |     |     |     |     |     | mation is | only added | to  | the data | structure | when | there it is |
| --- | --- | --- | --- | --- | --- | --------- | ---------- | --- | -------- | --------- | ---- | ----------- |
requestedduringrendering.Infact,notalldataareneeded
ateachpointintime,asforagivenviewpoint,unnecessary
|     |     |     |     |     |     | details can | be omitted | using | LOD | schemes, | as  | previously |
| --- | --- | --- | --- | --- | --- | ----------- | ---------- | ----- | --- | -------- | --- | ---------- |
mentioned.Inparticular,theuseofocclusioncullingleads
toamuchsmallerdatasubsetthatstillproducesacomplete
image.
| Figure28:      | TransitionphasefromLOD |        |            | toLOD | :left:    |     |     |     |     |     |     |     |
| -------------- | ---------------------- | ------ | ---------- | ----- | --------- | --- | --- | --- | --- | --- | --- | --- |
|                |                        |        |            | k     | k+1       |     |     |     |     |     |     |     |
| LOD k; middle: | midway                 | in the | transition | all   | fragments |     |     |     |     |     |     |     |
Wecannotcompletelyexplorein-depthallsolutionsthat
| of both LODs | are drawn; | right: | LOD | ; Below: | First |                                                      |     |     |     |     |     |     |
| ------------ | ---------- | ------ | --- | -------- | ----- | ---------------------------------------------------- | --- | --- | --- | --- | --- | --- |
|              |            |        |     | k+1      |       | existforthemanydifferenttypesofinputdata,varyingfrom |     |     |     |     |     |     |
LOD
k+1 isgraduallyintroduceduntilallitsfragmentsare geometricmodels[WDS04],overpointclouds[WBB*07],to
drawn.Then,LOD kisgraduallyremovedbyrenderingfewer recentvolume-renderingapproaches[GMAG08,CNLE09].
andfewerfragments.Thetoptworowsshowtheresultofour
methodandafalsecolourillustration. To illustrate the principle, we will base our discussion
|     |     |     |     |     |     | on ray-tracing    | queries. |              | The main | observation |            | is that ray- |
| --- | --- | --- | --- | --- | --- | ----------------- | -------- | ------------ | -------- | ----------- | ---------- | ------------ |
|     |     |     |     |     |     | tracing is        | a useful | tool,        | not only | to produce  |            | images, but  |
|     |     |     |     |     |     | also to determine |          | data fetches | [WDS04]. |             | Typically, | scenes       |
significantly,astheviewisverysimilar.Instead,afewlocal
areorganizedinformofatree(Figure29illustratesseveral
| refinements | are usually | enough. | Consequently, | many | LOD |           |                      |     |     |        |         |             |
| ----------- | ----------- | ------- | ------------- | ---- | --- | --------- | -------------------- | --- | --- | ------ | ------- | ----------- |
|             |             |         |               |      |     | levels of | detail corresponding |     | to  | levels | in this | tree). Rays |
approachesrelyonacutfromthepreviousframetofindthe
thentraversethetreeandtestgeometryintersectionsineach
| new representation | [XV96, | Hop97]. | Due | to the | coherence |     |     |     |     |     |     |     |
| ------------------ | ------ | ------- | --- | ------ | --------- | --- | --- | --- | --- | --- | --- | --- |
traversednode.Theideaisthatinitiallyeachnodeofthetree
| from one | frame to the next, | it is | sometimes | even | useful to |              |     |      |                |               |     |        |
| -------- | ------------------ | ----- | --------- | ---- | --------- | ------------ | --- | ---- | -------------- | ------------- | --- | ------ |
|          |                    |       |           |      |           | can be empty | and | will | only be filled | progressively |     | during |
enforcealimitednumberoflocalchangesinordertobound
|     |     |     |     |     |     | rendering. | Whenever | a ray | reaches | such | an empty | node, a |
| --- | --- | --- | --- | --- | --- | ---------- | -------- | ----- | ------- | ---- | -------- | ------- |
thecostofeachcutmodificationfromoneframetothenext.
|            |                 |            |       |        |           | data request | is triggered |              | and the        | ray potentially |      | stopped,  |
| ---------- | --------------- | ---------- | ----- | ------ | --------- | ------------ | ------------ | ------------ | -------------- | --------------- | ---- | --------- |
| Therefore, | such refinement | strategies | allow | for an | efficient |              |              |              |                |                 |      |           |
|            |                 |            |       |        |           | or traced    | against      | a simplified | representation |                 | that | fits into |
GPUimplementationonmodernhardware[HREB11].
|     |     |     |     |     |     | memory. | In this | way, the | rays themselves |     | control | the level |
| --- | --- | --- | --- | --- | --- | ------- | ------- | -------- | --------------- | --- | ------- | --------- |
Whileweassumedherethatthesceneisentirelypresentin ofdetail,aswellasfrustumculling,orocclusiontests.No
memory,forlargescenes,thiscanactuallybecomeimpossi- special handling of acceleration techniques is needed and,
ble.Nonetheless,asindicatedabove,onlyasmallpartofthe inparticular,asraystendtovarylittlefromoneviewtothe
treeisactuallyneeded(afewnodesaroundthederivedcut). next(e.g.forasmallandpurelyrotationalmovementofthe
camera,manyraysremainalmostunchanged),thetemporal
| Consequently, | it is possible | to restrict |     | memory usage | to a |     |     |     |     |     |     |     |
| ------------- | -------------- | ----------- | --- | ------------ | ---- | --- | --- | --- | --- | --- | --- | --- |
minimumbyremovingallunnecessarynodes.Thisprinciple redundancyisimplicitlyhandled.
leadstostreamingsolutionsthatwewillinvestigatenext.
|     |     |     |     |     |     | Such strategies |     | have | proven particularly |     | efficient | in the |
| --- | --- | --- | --- | --- | --- | --------------- | --- | ---- | ------------------- | --- | --------- | ------ |
contextofvolumerendering[GMAG08,CNLE09].Here,a
multi-resolutiondatarepresentationisarrangedinthetree,
5.10. Streaming
andwheneverdataaremissing,raysdonotneedtobecan-
5.10.1. Large-datavisualization celled,butcaninsteadwalkupthetreetoaccesslowerresolu-
tionversionsofthedata.Todealwiththememoryconstraints,
Streamingisaparticularlychallengingproblemwhendealing suchalgorithmstypicallyemployanLRUcachemechanism
withlargedatasets.Efficiencyisofparamountimportance, (least-recentlyused),i.e.newlyloadedelementswillreplace
| especially | due to the wealth | of  | scanned | data that | are often |     |     |     |     |     |     |     |
| ---------- | ----------------- | --- | ------- | --------- | --------- | --- | --- | --- | --- | --- | --- | --- |
thosethathavenotbeenaccessedforalongertime.Asele-
tremendousinsize.Thesedifficult-to-renderdatasetsexceed mentstendtobeactiveovercoherentperiodsoftime,such
availablememorycapacitiesbyfar. strategiesproveparticularlyuseful.Theycanbeimplemented
|     |     |     |     |     |     |     |     |     |     | (cid:2)c | 2012TheAuthors |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | -------------- | --- |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2400 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
Figure29: Onthebasisofvolume-datastreamingalgorithms,itisahierarchicalscenerepresentation.Here,severallevelsof
detailareillustrated.Theresolutionisswitchedautomaticallyduringtheray-tracingstep,dependingonthedistance.Notall
dataareinmemoryatonce,onlythepartsthatareactuallycurrentlyunderuseresideinmemory.
very efficiently on modern GPUs [CNSE10] and can even processthroughtheuseofobjectmotionvectors[FE09]that
serveinthecontextofglobalillumination[CNS*11]. areappliedtopredictpixelmotion.TheTCoftheanimation
inthesceneisdirectlyexploited.Thissolutioncanbevery
|     |     |     |     |     | successful | and enable | higher | compression |     | [WKC94] | than |
| --- | --- | --- | --- | --- | ---------- | ---------- | ------ | ----------- | --- | ------- | ---- |
5.10.2. Remoterendering
standardmatchingtechniques.
| Remote rendering | is trend | that is | now receiving | increased |            |          |     |            |     |         |           |
| ---------------- | -------- | ------- | ------------- | --------- | ---------- | -------- | --- | ---------- | --- | ------- | --------- |
|                  |          |         |               |           | It is also | possible | to  | go further | and | rely on | the scene |
attention.ManycompaniessuchasOnLive,OTOYorGaikai
|              |                  |         |            |           | attributes | for reconstruction |                 | purposes. |            | In fact, | the pre-   |
| ------------ | ---------------- | ------- | ---------- | --------- | ---------- | ------------------ | --------------- | --------- | ---------- | -------- | ---------- |
| focus on the | particular topic | of game | streaming. | In such a |            |                    |                 |           |            |          |            |
|              |                  |         |            |           | viously    | discussed          | spatio-temporal |           | upsampling |          | strategies |
scenario,itisvitaltoexploitTCinordertoreducebandwidth
|     |     |     |     |     | (Section | 5.6) are | very good | candidates |     | for application | in  |
| --- | --- | --- | --- | --- | -------- | -------- | --------- | ---------- | --- | --------------- | --- |
andcomputationaleffortontheserverside.
astreamingcontext[PHE*11].Suchacombinationhassev-
eraladvantages.Notonlythebandwidth,butalsotheserver
Inmostcases,theunderlyingtechnologyforgamestream-
ing is closely related to video compression, with a few workload is tackled (only small-resolution images are pro-
exceptions, which transfer API calls directly to the client ducedandtransferred).Furthermore,asthepreviousframe
[NDS*08],butsuchanarchitectureassumesveryadvanced isstillpresentontheclientwhenthenewframeissupposed
clienthardwarethatcandealwithallrenderingcommands. tobereconstructed,thealgorithmcanexploitthisknowledge
duringcompressionandrelyonthesevaluesaspredictorsfor
Video-encoded rendering does not require a powerful statistics-basedencodingschemes[PHE*11].
client,butthebandwidthrequirementscanbehigh.Hence,
temporalredundancyandperceptuallimitationsareacrucial Thisfieldofresearchisstillrelativelyyoungandislikely
|     |     |     |     |     | to evolve | significantly, | but | the | mentioned | recent | advances |
| --- | --- | --- | --- | --- | --------- | -------------- | --- | --- | --------- | ------ | -------- |
componentforsuchencodingalgorithms.Forexample,itis
illustratetheimportanceofexploitingTCinthiscontext.
possibletoexploitthereducedaccuracyofthehumanvisual
systemtopre-filterin-betweenframestoreducetherequired
5.11. Onlinevisibilityculling
bandwidth[FB08].
|     |     |     |     |     | Culling techniques |     | like | view-frustum | culling | [AM00] | and |
| --- | --- | --- | --- | --- | ------------------ | --- | ---- | ------------ | ------- | ------ | --- |
Usually,videoencodingmakesuseofso-calledI-frames
|     |     |     |     |     | visibility | culling | are important |     | acceleration | techniques | for |
| --- | --- | --- | --- | --- | ---------- | ------- | ------------- | --- | ------------ | ---------- | --- |
thatareonlyinternallyencoded(i.e.donotrelyonprevious
|                   |             |         |       |              | rasterization-based |     | real-time | rendering. |     | While | visibility is |
| ----------------- | ----------- | ------- | ----- | ------------ | ------------------- | --- | --------- | ---------- | --- | ----- | ------------- |
| or future frames) | and produce | precise | movie | information. |                     |     |           |            |     |       |               |
TheseI-framesarerareandcompletedbyP-framesthatrely often pre-processed in a lengthy offline step, online visi-
|              |              |           |        |              | bility culling | algorithms |     | compute | visibility | on  | the fly for |
| ------------ | ------------ | --------- | ------ | ------------ | -------------- | ---------- | --- | ------- | ---------- | --- | ----------- |
| on previous, | and B-frames | that make | use of | previous and |                |            |     |         |            |     |             |
thecurrentviewpoint.Typicallydirecthardwarequeriesare
| following images. | The latter | type | delivers quality-wise | su- |     |     |     |     |     |     |     |
| ----------------- | ---------- | ---- | --------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
used,so-calledocclusionqueries.Acommonuseofocclu-
periorresults,butisdifficulttoexploitforreal-timeapplica-
sionqueriesistoconservativelytestthevisibilityofasimple
tions.Becauseofthedependencyonfutureframes,adelay
isenforced,whichcanbeparticularlyproblematicforlower proxy geometry, e.g. the bounding box of a more complex
| framerates.Furthermore,intheextremecase,ifaframedrop |     |     |     |     | object. |     |     |     |     |     |     |
| ---------------------------------------------------- | --- | --- | --- | --- | ------- | --- | --- | --- | --- | --- | --- |
occurs,verynoticeableartefactscanarise.
5.11.1. ExploitingTC
| A complete | survey of video | encoding | goes | beyond the |     |     |     |     |     |     |     |
| ---------- | --------------- | -------- | ---- | ---------- | --- | --- | --- | --- | --- | --- | --- |
scopeofthisdocument.Here,wewilldescribesomepartic- The major challenge for any online culling algorithm is to
ularinsightsthatrelateto3Drendering.Videocompression reducetheoverheadcausedbythevisibilitycalculations(the
forrenderingshouldexploittheparticularityofthecontent. so-called occlusion queries), which can become unaccept-
Oneexampleisthatmanyattributescanbeextractedfrom ableinsituationswhenmostobjectsinthescenearevisible.
the3Dsceneitself,whichcanthenbeusedtoimprovethe Hence, it is vital to exploit TC, assuming that objects that
compression algorithms. One can accelerate the encoding are(in)visibleinoneframearelikelytoremain(in)visible
|     |     |     |     |     |     |     |     |     |     | (cid:2)c 2012TheAuthors |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------------------- | --- |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2401
infutureframes.UsingTC,wecansubstantiallyreducethe
| number | of issued occlusion | queries, | as well as | hide their |     |     |     |     |
| ------ | ------------------- | -------- | ---------- | ---------- | --- | --- | --- | --- |
latency.
Thefollowinggeneralstrategyisimplementedindifferent
| forms by  | all state-of-the-art  | occlusion | culling  | algorithms: |     |     |     |     |
| --------- | --------------------- | --------- | -------- | ----------- | --- | --- | --- | --- |
| First, an | algorithm establishes | a visible | front by | rendering   |     |     |     |     |
thoseobjectsthatwerevisibleinthepreviousframe.Then,
| it queries   | the visibility | of the previously | invisible     | objects |     |     |     |     |
| ------------ | -------------- | ----------------- | ------------- | ------- | --- | --- | --- | --- |
| against this | visible front. | Finally, to       | keep overdraw | low, it |     |     |     |     |
updatesthevisibilityclassificationsoftheobjectsfromthe
| visible front. | This can be | done in | a lazy manner, | e.g. by |     |     |     |     |
| -------------- | ----------- | ------- | -------------- | ------- | --- | --- | --- | --- |
n
| querying | each object every | frames | (assuming | coherence |     |     |     |     |
| -------- | ----------------- | ------ | --------- | --------- | --- | --- | --- | --- |
overseveralframes).Thecleverhierarchicalz-bufferalgo-
| rithm proposed | by [GKM93]    | uses            | both spatial | hierarchies |           |                                          |     |     |
| -------------- | ------------- | --------------- | ------------ | ----------- | --------- | ---------------------------------------- | --- | --- |
|                |               |                 |              |             | Figure30: | Comparisonofviewfrustumculling(VFC),view |     |     |
| and TC         | in the manner | described above | for maximal  | effi-       |           |                                          |     |     |
frustumcullingandpotentiallyvisiblesets(VFC+PVS),and
ciency. To accelerate visibility queries, it maintains a two- onlinevisibilitycullingusingCHC++[BMW*09].
foldhierarchy—animagepyramidoverthez-bufferandan
octreehierarchyovertheobjects.Thefeasibilityofthisal-
gorithmsuffersfromthedrawbackthatonlypartsofitare oftemporalandspatialcoherence.ItextendstheCHCalgo-
supportedbythehardware. rithmwithacoupleofsimplebuteffectiveoptimizations.
|     |     |     |     |     | CHC++ | issues batches of queries | instead of individual |     |
| --- | --- | --- | --- | --- | ----- | ------------------------- | --------------------- | --- |
queries.Thisisbasedontheobservationthatahugeportion
5.11.2. Coherenthierarchicalculling(CHC)
oftheindividualquerycostinCHCiscausedbyGPUstate
| Beginning | with the NVIDIA | GeForce | 3 graphics | card, |     |     |     |     |
| --------- | --------------- | ------- | ---------- | ----- | --- | --- | --- | --- |
changesduetotheconstantinterleavingofrenderandquery
| hardware-accelerated | occlusion | queries | can be | issued for |     |     |     |     |
| -------------------- | --------- | ------- | ------ | ---------- | --- | --- | --- | --- |
mode(e.g.depthwriteon/off).Thecoherenceamongnodes
a batch of rendered geometry. While hardware occlusion inabatchisexploitedbyassumingthatmutualocclusionof
queriesarefast,thequeriesstillcomewithanon-negligible thesenodesisnotrelevant.
cost,andtheyhaveacertainlatencyuntilthequeryresultis
available on the CPU. Algorithms like the CHC algorithm CHC++compilesmulti-queries,whichareabletocover
[BWPP04]utilizeTCtoavoidsuchCPUstallsandfillthe morenodesbyasingleocclusionquery.Thismethodisable
toreducethenumberofqueriesforpreviouslyinvisiblenodes
latencyinameaningfulway.
uptoanorderofmagnitudebymakingbetteruseofTC.The
Thealgorithmexploitstemporalandspatialcoherenceby
decisionofincludinganodeinamulti-queryisbasedonits
identifyinginvisiblesubtrees.Toavoidwastedinteriornode
history.Nodesthatwereinvisibleforalongtimearelikelyto
queries,itstartsissuingqueriesatthepreviouscutinthehier-
stayinvisible;hence,theycanbehandledbyasinglequery.
archy(i.e.itqueriespreviouslyinvisiblesubtreesandvisible A failed multi-query means that the nodes must be tested
leaves).Furthermore,CHCassumesthatpreviouslyvisible individually,wastingonequerywhileincreasingtheoverall
leavesstayvisible,andneverwaitsfortheirqueryresult.In-
numberofqueriesbyone.Hence,theauthorsintroduceda
stead,thesenodesarealwaysrenderedinthecurrentframe.
cost-benefitmodel(basedonthelikelihoodofanodetostay
Theirvisibilityclassificationsareupdatedforthenextframe
invisible)whichminimizesthenumberofqueries.Notethat
once the result is available. For this purpose, the pending thenodescanbespatiallycompletelyunrelated.
queriesaremanagedinadedicatedqueryqueue.Fortunately,
hardwareocclusionqueriesprovideacheapwaytocheckif Lazilyissuingqueriesforpreviouslyvisiblenodesevery
aqueryresultisavailable.Thisway,itispossibletodosome nframes(whichwasanoptioninCHC)hasthedangerof
traversalandrenderingontheCPU,whiletheGPUisbusy sudden frame rate drops. These happen because of many
queriesbeingissuedinthesameframeduetosimultaneous
computingthequeryresults,avoidingCPUstallsandGPU
visibilitychanges(e.g.allrooftopsofatownbecomevisible
starvation.
inthesameframe).Toavoidthisnegativeeffectofcoherence,
|                              |     |     |     |     | CHC++ applies           | a temporally jittered | sampling pattern | for |
| ---------------------------- | --- | --- | --- | --- | ----------------------- | --------------------- | ---------------- | --- |
| 5.11.3. MakingfurtheruseofTC |     |     |     |     | schedulingthosequeries. |                       |                  |     |
TheoriginalCHCalgorithmworkssufficientlywellinmany Figure 30 shows timings in the Powerplant scene with
situations, but still suffers from considerable overhead be- 12M triangles (using a NVIDIA GeForce 280 GTX). In-
cause of the large overall number of queries and the rela- terestingly, online visibility culling with CHC++ is typi-
tivelyhighcostofindividualqueries.TheCHC++algorithm cally faster than rendering based on preprocessed poten-
[MBW08]addressesthesedrawbacksbymakingbetteruse tiallyvisiblesets(PVSs).Thisisbecausethecomputational
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2402 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
overheadofCHC++islessthantherenderingoverheaddue Besidesmorecolours,resolutionanddetailscanalsobe
tothemoreconservativepreprocessedvisibilitysolution(i.e. addressed.Itisknownthatobjectdiscriminationismoresuc-
itoverestimatestheobjectsvisiblefromthecurrentviewpoint cessfulforsub-pixelcamerapanningthanforcorresponding
asvisibilityisstoredperregion). staticframes[KDT05,BSH06].Didyketal.[DER*10a]fur-
therexploredthisobservationbytakingintoaccounttheTC
|     |     |     |     | of eye movement | for apparent | resolution | enhancement. | In  |
| --- | --- | --- | --- | --------------- | ------------ | ---------- | ------------ | --- |
5.12. Temporalperception other words, they are able to produce the illusion of high
ThisreportpresentedseveralalgorithmsthatexploitTCof resolutiononalow-resolutionscreen,andthereby,evensur-
passthephysicalboundaries.Moreprecisely,theirsetupisa
| data, leveraging | the redundancy | of information | over time. |     |     |     |     |     |
| ---------------- | -------------- | -------------- | ---------- | --- | --- | --- | --- | --- |
low-resolutionscreenonwhichmovingcontentisdisplayed
| But, in fact,  | TC can also be | used in an inverse  | manner to  |           |                    |         |                 |         |
| -------------- | -------------- | ------------------- | ---------- | --------- | ------------------ | ------- | --------------- | ------- |
|                |                |                     |            | at a high | refresh rate. When | the eye | starts tracking | the in- |
| produce richer | content by     | exploiting elements | of percep- |           |                    |         |                 |         |
formationonthescreen,severalframeswillbesuccessively
tion,whichseemstobeaverypromisingavenueforfuture
endeavours.Evenphysicallyincoherentsignalsofhighvari- integratedontheretina.Bypredictingtheeyemovement,it
|     |     |     |     | is possible | to derive an image | sequence | such that the | inte- |
| --- | --- | --- | --- | ----------- | ------------------ | -------- | ------------- | ----- |
ancecanbeperceivedastemporallycoherentundercertain
|     |     |     |     | grated response | on the retina | approaches | a high-resolution |     |
| --- | --- | --- | --- | --------------- | ------------- | ---------- | ----------------- | --- |
circumstances.Asimpleexampleisaflashlightstrobingat
|     |     |     |     | image content. | The accuracy | of the | tracking is assured | by  |
| --- | --- | --- | --- | -------------- | ------------ | ------ | ------------------- | --- |
veryhighfrequency.Atsomepoint,wewillnolongerbeable
thehumanvisualsystem’ssmooth-pursuiteyemotion.This
toseetheflickeringeffectandperceiveacoherentlighting.
Infact,CRTscreensmadedirectuseoftheseobservations. mechanismleadstoanalmostperfectstabilizationforsteady
0.625−2.5◦
|                                                  |     |     |     | linear motion | with velocities | in the | range of |     |
| ------------------------------------------------ | --- | --- | --- | ------------- | --------------- | ------ | -------- | --- |
| WhenworkingwithsuchperceptualTC,manynewpossibil- |     |     |     | s−1           |                 |        |          |     |
[LRP*06].Thelow-resolutionimagesequenceitselfis
itiesbecomeavailable.Here,wewillfocusontwoexamples
derivedusinganoptimizationframeworkthattakeseyein-
(colourandresolutionincrease)thatrepresentfirststepsin
|     |     |     |     | tegration | and flicker perception | into | account to ensure | that |
| --- | --- | --- | --- | --------- | ---------------------- | ---- | ----------------- | ---- |
thisdirectionofresearch.
thissequenceintegratesproperlyontheretina.Thesolution
Oneoftheoldestexamplestoenrichgraphicsbyexploit- hasrecentlybeenextendedtogeneralanimationsequences
ing temporal effects is to rely on flickering to increase the includingarbitrarymovementsandgeneralscenesbyassum-
computer’s colour palette. The most prominent representa- ingtheeyemovementtoberelatedtotheunderlyingoptical
| tivesofsuchatechniqueareDLPprojectors,whichdisplay, |     |     |     | flow[TDR*11]. |     |     |     |     |
| --------------------------------------------------- | --- | --- | --- | ------------- | --- | --- | --- | --- |
inacoherentway,thethreecolourchannelsofanimagein
| rapidsuccession.Theseseparatesignalsarethenintegrated |                     |             |                | 6. Summary |     |     |     |     |
| ----------------------------------------------------- | ------------------- | ----------- | -------------- | ---------- | --- | --- | --- | --- |
| by the eye                                            | so that an observer | perceives a | fully coloured |            |     |     |     |     |
image. In this report, we have described real-time rendering tech-
niquesthattakeadvantageofTCbyreusingexpensivecal-
SimilartotheDLPprinciple,onecanincreasetheavailable culationsfrompreviouslyrenderedframes.Asaresult,both
coloursofascreenormachine.Backwhencolourpalettes
performanceandqualityofmanycommonreal-timerender-
werelimited,havingdarkenedtintsofcolours(e.g.forshad-
ingtaskscanbeimproved.
ows)wasnotalwayspossible.Byflickeringthecorrespond-
ingelementsonthescreen,asimplesolutiontoextendthe We started by showing that real-time rendering applica-
palette was born. For an observer, these flickered colours tions exhibit a significant amount of spatio-TC, thus moti-
mix because at higher frame rates, the eye no longer dis- vatingdatareuseinshadingcomputations.Wethenbriefly
tinguishes each frame individually. The same procedure is surveyedthehistoricalapproachesfocusedonofflinemeth-
often employed in LCD screens under the name of frame odsbeforedescribingthereal-timetechniqueswhichconsti-
rate control. In practice, the material is often limited to 6 tutethemainfocusofthisreport.We introducedthebasic
bitspercolourchannel,whereasthegraphicscardproduces algorithmforperformingreal-timereprojectionontheGPU.
8-bitcolourchannels.Thesolutionistorepresentfractional The approach allows the shader to efficiently query shad-
coloursbydisplayingtheimmediateneighboursinquicksuc- ing results from an earlier rendered frame (reverse repro-
cessionovertime[Art04].Again,theeyeintegrationdelivers jection),orsimilarly,mapashadingresultfromthecurrent
theillusionthatwhatwasobservedontheretinaisactually frametothenextframe(forwardreprojection).Wethenana-
thefractionalcolourvalue. lyzedthequalityversusspeedtrade-offsassociatedwithdata
reuse.
Anotherwaytoinfluencecolourperceptioninvolvingthe
temporaldomainistomakeuseofadaptation.Whenlooking Wepresentedseveralapplicationsthattakeadvantageof
foralongertimeatabrightsource,thesourceimprintsits datareuse.Westartedwiththebasicapplicationofdirectly
image on our retina in form of an afterimage in opponent reusing results of an expensive shading computation, such
colours.Thisphenomenonrelatestoreceptorbleaching.By as the previous results of a procedural noise shader. For
makinguseofacomputationalmodelofthiseffect,themech- applications that accumulate results from multiple render-
anismcanbesimulatedandcanleadtoaperceivedincrease ings of the same scene, such as stereo, motion blur and
ofbrightness[RE12]. depth-of-field rendering, we showed how to reuse shading
|     |     |     |     |     |     |     | (cid:2)c 2012TheAuthors |     |
| --- | --- | --- | --- | --- | --- | --- | ----------------------- | --- |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2403
results from a ‘central frame’ when rendering the remain- Acknowledgements
| ing accumulated | frames, | thereby | reducing |     | rendering times |          |      |          |           |        |           |     |
| --------------- | ------- | ------- | -------- | --- | --------------- | -------- | ---- | -------- | --------- | ------ | --------- | --- |
|                 |         |         |          |     |                 | We would | like | to thank | the Intel | Visual | Computing | In- |
considerably.
|     |     |     |     |     |     | stitute (IVCI) | at  | Saarland | University, | the | French | National |
| --- | --- | --- | --- | --- | --- | -------------- | --- | -------- | ----------- | --- | ------ | -------- |
Some expensive per-pixel computations often require Research Agency (iSpace&Time), the People Programme
approximating an integral by combining multiple spatial (MarieCurieActions)oftheFP7(underREAGrantAgree-
samples,suchasshadowcomputation.Toaddressthosesce- mentno.290227)andtheAustrianScienceFund(FWF)for
narios,wedescribedhowtoamortizecomputationbycom- partialfundingofthiswork.
biningresultsfrommultipleframesinordertoachievebetter
resultsforanti-aliasing,pixel-correctshadowsandsoftshad-
References
ows,amongotherapplications.Usingreprojectionforthese
techniquesallowsforamuchlargernumberofsamplesfor [AH93] ADELSON S. J., HODGES L. F.: Stereoscopic ray-
the same rendering time budget. The amortized approach tracing.TheVisualComputer10,3(1993),127–144.
alsoallowsforasmoothlyvaryingshadingresultinsteadof
the‘allornothing’reusestrategyoftheearlierapplications [AH95] ADELSONS.J.,HODGESL.F.:Generatingexactray-
that either fully reuse the earlier results or compute it en- tracedanimationframesbyreprojection.IEEEComputer
GraphicsandApplications15,3(1995),43–52.
tirelyanew.Weshowedsignificantimprovementinquality
andspeedfortheseamortizedapproachesandanalyzedthe
[AM00] ASSARSSONU.,MO¨LLERT.:Optimizedviewfrustum
trade-offbetweenlagandaliasingintherenderedresult.We
cullingalgorithmsforboundingboxes.Journalofgraph-
alsoshowedhowTCcanbeusedtocomputenotonlyeffi-
ics,GPU,andgametools5,1(2000),9–22.
cientshadowsfromalightsource,butalsoefficientglobal
illuminationapproximationsthroughamortization.Wethen
|     |     |     |     |     |     | [And10] | ANDREEV | D.: Real-time |     | frame | rate up-conversion |     |
| --- | --- | --- | --- | --- | --- | ------- | ------- | ------------- | --- | ----- | ------------------ | --- |
presentedtechniquestocombinebothspatialandtemporal
forvideogames.InProceedingsofACMSIGGRAPH2010
upsamplingusingajointbilateralfilterthatconsiderssam-
Talks(2010).
| ples from | recently | rendered | frames, | and how | to increase |     |     |     |     |     |     |     |
| --------- | -------- | -------- | ------- | ------- | ----------- | --- | --- | --- | --- | --- | --- | --- |
frameratesbygeneratingnewintermediateframesbytaking
|     |     |     |     |     |     | [Art04] ARTAMONOV |     | O.: | X-bit’s | guide: | Contempo- |     |
| --- | --- | --- | --- | --- | --- | ----------------- | --- | --- | ------- | ------ | --------- | --- |
advantageofTC.
|     |     |     |     |     |     | rary | lcd monitor |     | parameters | and | characteristics. |     |
| --- | --- | --- | --- | --- | --- | ---- | ----------- | --- | ---------- | --- | ---------------- | --- |
http://www.xbitlabs.com/articles/monitors/display/lcd-
Finally,weshowedhowTCcanbeusedtoimprovequal-
guide_11.html.AccessedOctober2004.
ityoraccelerateavarietyoftasks.Forwardreprojectionwas
| applied to | smoothly | advect | brush strokes | for | NPR of ani- |     |     |     |     |     |     |     |
| ---------- | -------- | ------ | ------------- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- |
[ATS94] ARVOJ.,TORRANCEK.,SMITSB.:Aframeworkfor
| mated scenes. | TC  | was used | to render | transition | phases for |     |     |     |     |     |     |     |
| ------------- | --- | -------- | --------- | ---------- | ---------- | --- | --- | --- | --- | --- | --- | --- |
theanalysisoferroringlobalilluminationalgorithms.In
discreteLODblending,therebyavoidingpoppingartefacts
SIGGRAPH’94:Proceedingsofthe21stAnnualConfer-
andcreatingasmoothtransitionbetweenlevelsofdetail.We
|     |     |     |     |     |     | ence on | Computer | Graphics |     | and Interactive | Techniques |     |
| --- | --- | --- | --- | --- | --- | ------- | -------- | -------- | --- | --------------- | ---------- | --- |
thenshowedhowTChasalsobeenexploredforstreaming
(NewYork,NY,USA,1994),ACM,pp.75–84.
content,suchasimprovedcompressionforremoterendering
of synthetic scenes (e.g. games), and large-data visualiza- [BBT11] BE´NARD P., BOUSSEAU A., THOLLOT J.: State-of-
tion.AnotherareathathasbeenexploredishowtouseTCto the-artreportontemporalcoherenceforstylizedanima-
accelerateocclusionculling.Finally,weshowedtechniques
tions.ComputerGraphicsForum30,8(December2011),
thatconsiderelementsofperceptionofthehumanvisualsys-
2367–2386.
teminordertoincreasetheapparentnumberofcoloursand
apparentresolutionoftheimage. [BCGF10] BE´NARDP.,COLEF.,GOLOVINSKIYA.,FINKELSTEIN
|     |     |     |     |     |     | A.: Self-similar |     | texture | for coherent |     | line stylization. | In  |
| --- | --- | --- | --- | --- | --- | ---------------- | --- | ------- | ------------ | --- | ----------------- | --- |
Tosummarize,thisreportsurveyedstrategiesforreusing
|                      |     |        |           |            |       | NPAR | 2010: | Proceedings | of  | the 8th | International | Sym- |
| -------------------- | --- | ------ | --------- | ---------- | ----- | ---- | ----- | ----------- | --- | ------- | ------------- | ---- |
| shading computations |     | during | real-time | rendering. | These |      |       |             |     |         |               |      |
posiumonNon-photorealisticAnimationandRendering
strategies are very generally applicable as demonstrated (NewYork,NY,USA,2010),ACMPress,pp.91–97.
| on a very | large number | of different |     | application | scenarios. |     |     |     |     |     |     |     |
| --------- | ------------ | ------------ | --- | ----------- | ---------- | --- | --- | --- | --- | --- | --- | --- |
Whilerelativelyrecent,thisresearchtrendhasalreadyfound [BFMZ94] BISHOP G., FUCHS H., MCMILLAN L., ZAGIER E.
| uses in the | gaming         | community.     | We          | hope that   | in this pro- |                  |             |            |          |             |            |          |
| ----------- | -------------- | -------------- | ----------- | ----------- | ------------ | ---------------- | ----------- | ---------- | -------- | ----------- | ---------- | -------- |
|             |                |                |             |             |              | J. S.: Frameless |             | rendering: | Double   | buffering   | considered |          |
| cess, we    | have convinced | the            | reader      | that taking | advantage    |                  |             |            |          |             |            |          |
|             |                |                |             |             |              | harmful.         | In SIGGRAPH |            | ’94:     | Proceedings | of         | the 21st |
| of TC can   | vastly         | reduce shading | computation |             | in a very    |                  |             |            |          |             |            |          |
|             |                |                |             |             |              | Annual           | Conference  | on         | Computer | Graphics    | and        | Interac- |
largenumberofrenderingscenarios.Withthecontinuedin- tiveTechniques(NewYork,NY,USA,1994),ACM,pp.
| creaseincomplexshadingeffects,framerates,screenreso- |     |     |     |     |     | 175–176. |     |     |     |     |     |     |
| ---------------------------------------------------- | --- | --- | --- | --- | --- | -------- | --- | --- | --- | --- | --- | --- |
lutionandrenderinghardwarefeatures,weexpectthattech-
niques that take advantage of TC will become even more [BFP*11] BUCHHOLZ B., FARAJ N., PARIS S., EISEMANN
prevalent.
|     |     |     |     |     |     | E., BOUBEKEUR |     | T.: | Spatio-temporal |     | analysis | for |
| --- | --- | --- | --- | --- | --- | ------------- | --- | --- | --------------- | --- | -------- | --- |
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2404 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
parameterizinganimatedlines.InProceedingsoftheIn- Annual Conference on Computer Graphics and Interac-
ternationalSymposiumonNon-PhotorealisticAnimation tiveTechniques(NewYork,NY,USA,1993),ACM,pp.
| andRendering(NPAR)(2011). |     |     |     |     | 279–288. |     |     |     |     |     |
| ------------------------- | --- | --- | --- | --- | -------- | --- | --- | --- | --- | --- |
[BJ88] BADTJr.S.:Twoalgorithmsfortakingadvantageof [DDM03] DAMEZC.,DMITRIEVK.,MYSZKOWSKIK.:Stateof
temporalcoherenceinraytracing.TheVisualComputer theartinglobalilluminationforinteractiveapplications
4(1988),123–132. andhigh-qualityanimations.ComputerGraphicsForum
22,1(March2003),55–77.
| [BM05] BENNETT | E. P., MCMILLAN | L.: Video | enhancement |     |     |     |     |     |     |     |
| -------------- | --------------- | --------- | ----------- | --- | --- | --- | --- | --- | --- | --- |
using per-pixel virtual exposures. ACM Transactions on [DER*10a] DIDYKP.,EISEMANNE.,RITSCHELT.,MYSZKOWSKI
Graphics24,3(2005),845–852. K.,SEIDELH.-P.:Apparentdisplayresolutionenhancement
formovingimages.ACMTransactionsonGraphics(Pro-
| [BMW*09] | BITTNER J., MATTAUSCH | O., WONKA | P., | HAVRAN |     |     |     |     |     |     |
| -------- | --------------------- | --------- | --- | ------ | --- | --- | --- | --- | --- | --- |
ceedingsofSIGGRAPH2010,LosAngeles)29,3(2010).
| V., WIMMER | M.: Adaptive | global visibility | sampling. | In  |     |     |     |     |     |     |
| ---------- | ------------ | ----------------- | --------- | --- | --- | --- | --- | --- | --- | --- |
SIGGRAPH ’09: Proceedings of the ACM SIGGRAPH [DER*10b] DIDYKP.,EISEMANNE.,RITSCHELT.,MYSZKOWSKI
2009Papers(NewYork,NY,USA,2009),ACM. K., SEIDEL H.-P.: Perceptually-motivated real-time tem-
|     |     |     |     |     | poral upsampling | of  | 3D content | for | high-refresh-rate |     |
| --- | --- | --- | --- | --- | ---------------- | --- | ---------- | --- | ----------------- | --- |
[BSD08] BAVOIL L., SAINZ M., DIMITROV R.: Image-space displays. Computer Graphics Forum 29, 2 (2010),
| horizon-based | ambient | occlusion. In SIGGRAPH |     | ’08: |     |     |     |     |     |     |
| ------------- | ------- | ---------------------- | --- | ---- | --- | --- | --- | --- | --- | --- |
713–722.
ProceedingsoftheACMSIGGRAPH2008talks(2008).
|         |                  |                |        |        | [DRE*10] DIDYKP.,RITSCHELT.,EISEMANNE.,MYSZKOWSKI |     |     |     |     |     |
| ------- | ---------------- | -------------- | ------ | ------ | ------------------------------------------------- | --- | --- | --- | --- | --- |
| [BSH06] | BIJL P., SCHUTTE | K., HOGERVORST | M. A.: | Appli- |                                                   |     |     |     |     |     |
K.,SEIDELH.-P.:Adaptiveimage-spacestereoviewsyn-
| cability | of TOD, MTDP, | MRT and DMRT | for dynamic |     |     |     |     |     |     |     |
| -------- | ------------- | ------------ | ----------- | --- | --- | --- | --- | --- | --- | --- |
thesis.InProceedingsoftheVision,ModelingandVisu-
imageenhancementtechniques.InProceedingsoftheSo- alizationWorkshop(112010).
cietyofPhoto-OpticalInstrumentationEngineers(SPIE)
ConferenceSeries(2006),vol.6207. [DWWL05] DAYAL A., WOOLLEY C., WATSON B., LUEBKE
D.P.:Adaptiveframelessrendering.InProceedingsofthe
[BWPP04] BITTNER J., WIMMER M., PIRINGER H., EurographicsSymposiumonRenderingTechniques,Kon-
| PURGATHOFER | W.: Coherent | hierarchical | culling: | Hard- |     |     |     |     |     |     |
| ----------- | ------------ | ------------ | -------- | ----- | --- | --- | --- | --- | --- | --- |
stanz,Germany,June29–July1,2005(2005),O.Deussen,
wareocclusionqueriesmadeuseful.ComputerGraphics
|     |     |     |     |     | A. Keller, | K. Bala, P. | D. D. W. | Fellner, | S. N. | Spencer |
| --- | --- | --- | --- | --- | ---------- | ----------- | -------- | -------- | ----- | ------- |
Forum 23, 3 (September 2004), 615–624. [Proceedings (Eds.).EurographicsAssociation,Konstanz,Germany,pp.
| EUROGRAPHICS2004.] |     |     |     |     | 265–275. |     |     |     |     |     |
| ------------------ | --- | --- | --- | --- | -------- | --- | --- | --- | --- | --- |
[CNLE09] CRASSIN C., NEYRET F., LEFEBVRE S., EISEMANN [EASW09] EISEMANN E., ASSARSSON U., SCHWARZ M.,
E.: Gigavoxels : Ray-guided streaming for efficient and WIMMER M.: Casting shadows in real time. In Proceed-
| detailed | voxel rendering. | In Proceedings | of the | ACM |             |              |     |           |         |       |
| -------- | ---------------- | -------------- | ------ | --- | ----------- | ------------ | --- | --------- | ------- | ----- |
|          |                  |                |        |     | ings of the | ACM SIGGRAPH |     | Asia 2009 | Courses | (Dec. |
SIGGRAPHSymposiumonInteractive3DGraphicsand
2009).
Games(I3D)(Boston,MA,USA,February2009),ACM
| Press. |     |     |     |     | [EASW10] | EISEMANN E., | ASSARSSON | U., | SCHWARZ | M., |
| ------ | --- | --- | --- | --- | -------- | ------------ | --------- | --- | ------- | --- |
WIMMERM.:Shadowalgorithmsforreal-timerendering.
[CNS*11] CRASSIN C., NEYRET F., SAINZ M., GREEN S., InProceedingsoftheEurographicsTutorial(Dec.2010).
EISEMANNE.:Interactiveindirectilluminationusingvoxel
conetracing.ComputerGraphicsForum30,7(2011),pp. [ED04] EISEMANN E., DURAND F.: Flash photography en-
1921–1930.doi:10.1111/j.1467-8659.2011.02063.x. hancement via intrinsic relighting. ACM Transactions
|          |                    |               |          |     | on Graphics | (Proceedings | of  | Siggraph | Conference) | 23  |
| -------- | ------------------ | ------------- | -------- | --- | ----------- | ------------ | --- | -------- | ----------- | --- |
| [CNSE10] | CRASSIN C., NEYRET | F., SAINZ M., | EISEMANN | E.: |             |              |     |          |             |     |
(2004),673–678.
EfficientRenderingofHighlyDetailedVolumetricScenes
withGigaVoxels.InGPUPro.A.K.Peters(Ed.),Natick, [ED07a] EISEMANNE.,DE´CORETX.:Onexacterrorbounds
MA,USA,(2010),ch.X.3,pp.643–676. for view-dependent simplification. Computer Graphics
Forum26,2(2007),202–213.
| [CT81] COOK | R. L., TORRANCE | K. E.: A reflectance |     | model |     |     |     |     |     |     |
| ----------- | --------------- | -------------------- | --- | ----- | --- | --- | --- | --- | --- | --- |
forcomputergraphics.InSIGGRAPH’81:Proceedingsof [ED07b] EISEMANNE., DE´CORET X.: Visibility sampling on
the8thAnnualConferenceonComputerGraphicsandIn- gpu and applications. Computer Graphics Forum (Pro-
teractiveTechniques(NewYork,NY,USA,1981),ACM, ceedingsofEurographics2007)26,3(2007),535–544.
pp.307–316.
|     |     |     |     |     | [ESAW11] | EISEMANN E., | SCHWARZ | M., | ASSARSSON | U., |
| --- | --- | --- | --- | --- | -------- | ------------ | ------- | --- | --------- | --- |
[CW93] CHENS.E.,WILLIAMSL.:Viewinterpolationforim- WIMMERM.:Real-TimeShadows.A.K.Peters(Ed.).CRC
agesynthesis.InSIGGRAPH’93:Proceedingsofthe20th Press,Natick,MA,USA,(2011).
|     |     |     |     |     |     |     |     | (cid:2)c 2012TheAuthors |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------------------- | --- | --- |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2405
[FB08] FUJIBAYASHI A., BOON C. S.: A masking model for CSDepartment,CarnegieMellonUniversity,Jan.1997.
motionsharpeningphenomenoninvideosequences.IE- http://www.cs.cmu.edu/ph.
ICETransactionsonFundamentalsofElectronics,Com-
|             |     |          |          |        |           | [HLHS03] | HASENFRATZJ.-M.,LAPIERREM.,HOLZSCHUCHN., |     |     |     |     |     |
| ----------- | --- | -------- | -------- | ------ | --------- | -------- | ---------------------------------------- | --- | --- | --- | --- | --- |
| munications | and | Computer | Sciences | E91-A, | 6 (2008), |          |                                          |     |     |     |     |     |
1408–1415. SILLIONF.:Asurveyofreal-timesoftshadowsalgorithms.
ComputerGraphicsForum22,4(Dec.2003),753–774.
[FC08] FOXM.,COMPTONS.:Ambientocclusivecreaseshad- [State-of-the-ArtReviews.]
ing.GameDeveloperMagazine(March2008).
[Hop97] HOPPEH.:View-dependentrefinementofprogres-
[FE09] FECHTELERP.,EISERTP.:Depthmapenhancedmac- sivemeshes.InProceedingsofSIGGRAPH(1997).
roblockpartitioningforH.264videocodingofcomputer
|     |     |     |     |     |     | [HREB11] | HOLLA¨NDER | M., | RITSCHEL |     | T., EISEMANN | E., |
| --- | --- | --- | --- | --- | --- | -------- | ---------- | --- | -------- | --- | ------------ | --- |
graphicscontent.InProceedingsoftheInternationalCon-
|     |     |     |     |     |     | BOUBEKEUR | T.: | Manylods: | Parallel | many-view |     | level-of- |
| --- | --- | --- | --- | --- | --- | --------- | --- | --------- | -------- | --------- | --- | --------- |
ferenceonImageProcessing(2009),pp.3441–3444.
|     |     |     |     |     |     | detail selection |     | for real-time |     | global illumination. |     | Com- |
| --- | --- | --- | --- | --- | --- | ---------------- | --- | ------------- | --- | -------------------- | --- | ---- |
[FPD08] FENG X.-F., PAN H., DALY S.: Comparisons of puterGraphicsForum(Proc.ofEGSR)(2011).
| motion-blur | assessment | strategies |     | for newly | emergent |     |     |     |     |     |     |     |
| ----------- | ---------- | ---------- | --- | --------- | -------- | --- | --- | --- | --- | --- | --- | --- |
LCD and backlight driving technologies. Journal of the [Jan01] JANSSEN R.: Computational Image Quality. Spie
SocietyforInformationDisplay16(2008),981–988. Press,Bellingham,Washington,DC,2001.
[GKM93] GREENEN.,KASSM.,MILLERG.:HierarchicalZ- [Kaj86] KAJIYA J. T.: The rendering equation. SIGGRAPH
buffervisibility.ComputerGraphics(ProceedingsofSIG- ComputerGraphics20,4(1986),143–150.
GRAPH’93)(1993),231–238.
|     |     |     |     |     |     | [KCLU07] | KOPF | J., COHEN |     | M. F., | LISCHINSKI | D., |
| --- | --- | --- | --- | --- | --- | -------- | ---- | --------- | --- | ------ | ---------- | --- |
UYTTENDAELEM.:Jointbilateralupsampling.ACMTrans-
[GMAG08] GOBBETTIE.,MARTONF.,ANTONIOJ.,GUITIANI.:
|     |     |     |     |     |     | actions | on Graphics | (Proceedings |     | of SIGGRAPH |     | 2007) |
| --- | --- | --- | --- | --- | --- | ------- | ----------- | ------------ | --- | ----------- | --- | ----- |
Asingle-passGPUraycastingframeworkforinteractive
| out-of-corerenderingofmassivevolumetricdatasets.The |     |     |     |     |     | 26,3(2007). |     |     |     |     |     |     |
| --------------------------------------------------- | --- | --- | --- | --- | --- | ----------- | --- | --- | --- | --- | --- | --- |
VisualComputer24,7(2008),797–806.
|     |     |     |     |     |     | [KDMF03] | KALNINS | R.  | D., DAVIDSON |     | P. L., | MARKOSIAN |
| --- | --- | --- | --- | --- | --- | -------- | ------- | --- | ------------ | --- | ------ | --------- |
[GW06] GIEGL M., WIMMER M.: Unpopping: Solving the L., FINKELSTEIN A.: Coherent stylized silhouettes. ACM
|     |     |     |     |     |     | Transactions |     | on Graphics | 22, | 3 (July | 2003), | 856– |
| --- | --- | --- | --- | --- | --- | ------------ | --- | ----------- | --- | ------- | ------ | ---- |
image-spaceblendproblemforsmoothdiscretelodtran-
861.
| sitions. Computer |     | Graphics | Forum | 26, 1 | (Mar. 2006), |     |     |     |     |     |     |     |
| ----------------- | --- | -------- | ----- | ----- | ------------ | --- | --- | --- | --- | --- | --- | --- |
46–49.
|     |     |     |     |     |     | [KDT05]     | KRAPELS     | K., DRIGGERS |                 | R. G., TEANEY |          | B.: Target- |
| --- | --- | --- | --- | --- | --- | ----------- | ----------- | ------------ | --------------- | ------------- | -------- | ----------- |
|     |     |     |     |     |     | acquisition | performance |              | in undersampled |               | infrared | im-         |
[HA90] HAEBERLIP.,AKELEYK.:Theaccumulationbuffer:
Hardwaresupportforhigh-qualityrendering.InProceed- agers:Staticimagerytomotionvideo.AppliedOptics44,
ings of SIGGRAPH ’90 (New York, NY, USA, 1990), 33(2005),7055–7061.
ACM,pp.309–318.
[Kel97] KELLERA.:Instantradiosity.InProceedingsofSIG-
[HBS03] HAVRAN V., BITTNER J., SEIDEL H.-P.: Exploiting GRAPH’97 (Aug.1997),ComputerGraphicsProceed-
ings,AnnualConferenceSeries,pp.49–56.
temporalcoherenceinraycastedwalkthroughs.InSCCG
’03:Proceedingsofthe19thSpringConferenceonCom-
|     |     |     |     |     |     | [KMM*02] | KALNINS | R.  | D., MARKOSIAN |     | L., MEIER | B. J., |
| --- | --- | --- | --- | --- | --- | -------- | ------- | --- | ------------- | --- | --------- | ------ |
puterGraphics(NewYork,NY,USA,2003),ACMPress,
|     |     |     |     |     |     | KOWALSKI | M.  | A., LEE | J. C., DAVIDSON |     | P. L., | WEBB M., |
| --- | --- | --- | --- | --- | --- | -------- | --- | ------- | --------------- | --- | ------ | -------- |
pp.149–155.
|     |     |     |     |     |     | HUGHES | J. F., | FINKELSTEIN | A.: | WYSIWYG | NPR: | Draw- |
| --- | --- | --- | --- | --- | --- | ------ | ------ | ----------- | --- | ------- | ---- | ----- |
[HDMS03] HAVRAN V., DAMEZ C., MYSZKOWSKI K., SEIDEL ingstrokesdirectlyon3Dmodels.ACMTransactionson
Graphics21,3(July2002),755–762.
| H.-P.: An | efficient  | spatio-temporal |      | architecture | for    |             |     |        |     |          |       |          |
| --------- | ---------- | --------------- | ---- | ------------ | ------ | ----------- | --- | ------ | --- | -------- | ----- | -------- |
| animation | rendering. | In EGRW         | ’03: | Proceedings  | of the |             |     |        |     |          |       |          |
|           |            |                 |      |              |        | [KP11] KASS | M., | PESARE | D.: | Coherent | noise | for non- |
14thEurographicsWorkshoponRendering(Aire-la-Ville,
photorealisticrendering.ACMTransactionsonGraphics
Switzerland,2003),Springer,pp.106–117.
30,4(Aug.2011),30:1–30:6.
[HEMS10] HERZOGR.,EISEMANNE.,MYSZKOWSKIK.,SEIDEL
|                        |               |            |                |        |              | [KTM*10]    | KNECHT    | M.,        | TRAXLER | C.,          | MATTAUSCH | O.,         |
| ---------------------- | ------------- | ---------- | -------------- | ------ | ------------ | ----------- | --------- | ---------- | ------- | ------------ | --------- | ----------- |
| H.-P.: Spatio-temporal |               | upsampling |                | on the | GPU. In Pro- |             |           |            |         |              |           |             |
|                        |               |            |                |        |              | PURGATHOFER |           | W., WIMMER | M.:     | Differential |           | instant ra- |
| ceedings of            | the Symposium |            | on Interactive |        | 3D Graphics  |             |           |            |         |              |           |             |
|                        |               |            |                |        |              | diosity     | for mixed | reality.   | In      | Proceedings  | of        | the Ninth   |
andGames(NewYork,NY,USA,2010),ACM.
IEEEandACMInternationalSymposiumonMixedand
|     |     |     |     |     |     | Augmented | Reality | (ISMAR’10) |     | (Seoul, | Korea, | October |
| --- | --- | --- | --- | --- | --- | --------- | ------- | ---------- | --- | ------- | ------ | ------- |
[HH97] HECKBERTP.S.,HERFM.:SimulatingSoftShadows
2010).
| with Graphics | Hardware. |     | Tech. Rep. | CMU-CS-97-104, |     |     |     |     |     |          |                |     |
| ------------- | --------- | --- | ---------- | -------------- | --- | --- | --- | --- | --- | -------- | -------------- | --- |
|               |           |     |            |                |     |     |     |     |     | (cid:2)c | 2012TheAuthors |     |
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2406 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
[KV04] KLOMPENHOUWER M. A., VELTHOVEN L. J.: Mo- InProceedingsoftheEurographicsSymposiumonPoint-
tion blur reduction for liquid crystal displays: Motion- BasedGraphics(2007),pp.101–108.
| compensated | inverse | filtering. | In Proc. | SPIE, | 5308, |         |                                       |     |     |     |     |
| ----------- | ------- | ---------- | -------- | ----- | ----- | ------- | ------------------------------------- | --- | --- | --- | --- |
|             |         |            |          |       |       | [MSW10] | MATTAUSCHO.,SCHERZERD.,WIMMERM.:High- |     |     |     |     |
(2004),pp.690–699.
|     |     |     |     |     |     | quality | screen-space | ambient | occlusion | using | tempo- |
| --- | --- | --- | --- | --- | --- | ------- | ------------ | ------- | --------- | ----- | ------ |
[Lan02] LANDIS H.: Production-ready global illumination. ral coherence. Computer Graphics Forum 29(8) (2010),
| In Proceedings | of  | the Conference | on  | SIGGRAPH | 2002 | 2492–2503. |     |     |     |     |     |
| -------------- | --- | -------------- | --- | -------- | ---- | ---------- | --- | --- | --- | --- | --- |
CourseNotes16(2002),2002.
|     |     |     |     |     |     | [NDS*08] | NAVEI.,DAVIDH.,SHANIA.,LAIKARIA.,EISERT |     |     |     |     |
| --- | --- | --- | --- | --- | --- | -------- | --------------------------------------- | --- | --- | --- | --- |
[LKR*96] LINDSTROMP.,KOLLERD.,RIBARSKYW.,HODGES P.,FECHTELERP.:Games@Largegraphicsstreamingarchi-
L.F.,FAUSTN.,TURNERG.A.:Real-time,continuouslevel tecture. In Proceedings of the Symposium on Consumer
ofdetailrenderingofheightfields.InProceedingsofSIG- Electronics(ISCE)(2008).
GRAPH(1996),pp.109–118.
|     |     |     |     |     |     | [NSL*07] | NEHABD.,SANDERP.V.,LAWRENCEJ.,TATARCHUK |     |     |     |     |
| --- | --- | --- | --- | --- | --- | -------- | --------------------------------------- | --- | --- | --- | --- |
[LRC*02] LUEBKED.,REDDY,M.,COHENJ.,VARSHNEYA., N., ISIDORO J. R.: Accelerating real-time shading with
WATSONB.,HUEBNERR.:LevelofDetailfor3DGraphics. reverse reprojection caching. In Proceedings of the
MorganKaufmann,NewYork,NY,USA,2002. 22ndACMSIGGRAPH/EUROGRAPHICSSymposiumon
GraphicsHardware(2007),pp.25–35.
| [LRP*06] LAIRD | J., | ROSEN | M., PELZ J., | MONTAG | E., DALY |     |     |     |     |     |     |
| -------------- | --- | ----- | ------------ | ------ | -------- | --- | --- | --- | --- | --- | --- |
S.: Spatio-velocity CSF as a function of retinal velocity [PFD05] PAN H., FENG X.-F., DALY S.: LCD motion blur
usingunstabilizedstimuli.InProceedingsoftheHuman modeling and analysis. In Proceedings of ICIP (2005),
| Vision and | Electronic | Imaging | XI (2006), | vol. | 6057 of | pp.21–24. |     |     |     |     |     |
| ---------- | ---------- | ------- | ---------- | ---- | ------- | --------- | --- | --- | --- | --- | --- |
SPIEProceedingsSeries,pp.32–43.
|     |     |     |     |     |     | [PHE*11] | PAJAKD.,HERZOGR.,EISEMANNE.,MYSZKOWSKI |     |     |     |     |
| --- | --- | --- | --- | --- | --- | -------- | -------------------------------------- | --- | --- | --- | --- |
[LS97] LENGYELJ.,SNYDERJ.:Renderingwithcoherentlay- K.,SEIDELH.-P.:Scalableremoterenderingwithdepthand
ers. In SIGGRAPH ’97: Proceedings of the 24th An- motion-flow augmented streaming. Computer Graphics
nual Conference on Computer Graphics and Interac- Forum30,2(2011).(Proc.ofEurographics.)
| tive Techniques | (New | York, | NY, USA, | 1997), | ACM |          |                                          |     |     |     |     |
| --------------- | ---- | ----- | -------- | ------ | --- | -------- | ---------------------------------------- | --- | --- | --- | --- |
|                 |      |       |          |        |     | [PSA*04] | PETSCHNIGGG.,SZELISKIR.,AGRAWALAM.,COHEN |     |     |     |     |
Press/Addison-WesleyPublishingCo.,pp.233–242.
M.,HOPPEH.,TOYAMAK.:Digitalphotographywithflash
[LSF10] LU J., SANDER P. V., FINKELSTEIN A.: Interactive and no-flash image pairs. ACM Transactions on Graph-
painterly stylization of images, videos and 3d anima- ics (Proceedings of Siggraph Conference) 23, 3 (2004),
| tions. In | Proceedings | of  | the Symposium | on  | Interactive | 664–672. |     |     |     |     |     |
| --------- | ----------- | --- | ------------- | --- | ----------- | -------- | --- | --- | --- | --- | --- |
3DGraphicsandGames(2010),pp.127–134.
|     |     |     |     |     |     | [QWQK00] | QU H., | WAN M., | QIN J., KAUFMAN |     | A.: Image |
| --- | --- | --- | --- | --- | --- | -------- | ------ | ------- | --------------- | --- | --------- |
[LSK*07] LAINES.,SARANSAARIH.,KONTKANENJ.,LEHTINEN basedrenderingwithstableframerates.InVISUALIZA-
J.,AILAT.:Incrementalinstantradiosityforreal-timein- TION ’00: Proceedings of the 11th IEEE Visualization
directillumination.InProceedingsofEurographicsSym- 2000 Conference (VIS 2000) (Washington, DC, USA,
posiumonRendering2007(2007),EurographicsAssoci- 2000),IEEEComputerSociety.
ation,pp.277–286.
|     |     |     |     |     |     | [RE12] RITSCHEL | T., | EISEMANN | E.: A computational |     | model |
| --- | --- | --- | --- | --- | --- | --------------- | --- | -------- | ------------------- | --- | ----- |
[MB95] MCMILLANL.,BISHOPG.:Head-trackedstereoscopic ofafterimages.ComputerGraphicsForum(Proc.EURO-
display using image warping. In Proceedings of SPIE GRAPHICS)31,2(May2012).
(1995),Vol.2409,pp.21–30.
|     |     |     |     |     |     | [REH*11] | RITSCHEL | T., EISEMANN | E., HA | I., SEIDEL | H.-P.: |
| --- | --- | --- | --- | --- | --- | -------- | -------- | ------------ | ------ | ---------- | ------ |
[MBW08] MATTAUSCH O., BITTNER J., WIMMER M.: Making imperfect shadow maps view-adaptive: High-
Chc++:Coherenthierarchicalcullingrevisited.Computer qualityglobalilluminationinlargedynamicscenes.Com-
GraphicsForum(ProceedingsofEurographics2008)27, puterGraphicsForum(presentedatEGSR2011)(2011).
3(Apr.2008),221–230.
|     |     |     |     |     |     | [RGK*08] | RITSCHEL | T., GROSCH | T., KIM | M. H., | SEIDEL H.- |
| --- | --- | --- | --- | --- | --- | -------- | -------- | ---------- | ------- | ------ | ---------- |
[Mit07] MITTRINGM.:Findingnextgen-cryengine2.InPro- P., DACHSBACHER C., KAUTZ J.: Imperfect shadow maps
ceedingsoftheConferenceonSIGGRAPH2007Course for efficient computation of indirect illumination. ACM
Notes,Course28,AdvancedReal-TimeRenderingin3D TransactionsonGraphics(Proc.SIGGRAPHASIA2008)
| GraphicsandGames,(NewYork,NY,USA,2007),ACM |     |     |     |     |     | 27,5(2008),129. |     |     |     |     |     |
| ------------------------------------------ | --- | --- | --- | --- | --- | --------------- | --- | --- | --- | --- | --- |
Press,pp.97–121.
|     |     |     |     |     |     | [RP94] REGAN | M., | POSE R.: Priority | rendering |     | with a vir- |
| --- | --- | --- | --- | --- | --- | ------------ | --- | ----------------- | --------- | --- | ----------- |
[MKC07] MARROQUIMR.,KRAUSM.,CAVALCANTIP.R.:Ef- tualrealityaddressrecalculationpipeline.InSIGGRAPH
ficientpoint-basedrenderingusingimagereconstruction. ’94: Proceedings of the 21st Annual Conference on
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering 2407
Computer Graphics and Interactive Techniques (New [SS00] SIMMONS M., SE´QUIN C. H.: Tapestry: A dynamic
York,NY,USA,1994),ACM,pp.155–162. mesh-baseddisplayrepresentationforinteractiverender-
|     |     |     |     |     | ing. In Proceedings | of the | 11th Eurographics | Workshop |
| --- | --- | --- | --- | --- | ------------------- | ------ | ----------------- | -------- |
[SaLY*08a] SITTHI-AMORNP.,LAWRENCEJ.,YANGL.,SANDER onRendering(2000),pp.329–340.
P.V.,NEHABD.:Animprovedshadingcacheformodern
GPUs.InProceedingsofGraphicsHardware(2008),pp. [SSMW09] SCHERZER D., SCHWA¨RZLER M., MATTAUSCH O.,
| 95–101. |     |     |     |     | WIMMERM.:Real-timesoftshadowsusingtemporalco- |     |     |     |
| ------- | --- | --- | --- | --- | --------------------------------------------- | --- | --- | --- |
herence.LectureNotesinComputerScience(LNCS)(Nov.
| [SaLY*08b] | SITTHI-AMORNP.,LAWRENCEJ.,YANGL.,SANDER |     |     |     | 2009). |     |     |     |
| ---------- | --------------------------------------- | --- | --- | --- | ------ | --- | --- | --- |
P.V.,NEHABD.,XIJ.:Automatedreprojection-basedpixel
|     |     |     |     |     | [SSS74] SUTHERLAND | I. E., | SPROULL R. F., SCHUMACKER | R.  |
| --- | --- | --- | --- | --- | ------------------ | ------ | ------------------------- | --- |
shaderoptimization.ACMTransactionsonGraphics27,
5(122008),127. A.: A characterization of ten hidden surface algorithms.
ACMComputingSurveys6,1(1974),1–55.
[SB95] SMITHS.M.,BRADYJ.M.:SUSAN—Anewapproach
tolowlevelimageprocessing.Tech.Rep.TR95SMS1c, [SW08] SCHERZERD.,WIMMERM.:Framesequentialinter-
polationfordiscretelevel-of-detailrendering.Computer
Chertsey,Surrey,UK,1995.
|     |     |     |     |     | Graphics Forum | (Proceedings | EGSR 2008) | 27, 4 (June |
| --- | --- | --- | --- | --- | -------------- | ------------ | ---------- | ----------- |
2008),1175–1181.
[Sch96] SCHAUFLERG.:Exploitingframetoframecoherence
inavirtualrealitysystem.InVRAIS’96:Proceedingsof
|     |     |     |     |     | [SW09] SMEDBERG | N., WRIGHT | D.: Rendering | techniques |
| --- | --- | --- | --- | --- | --------------- | ---------- | ------------- | ---------- |
the1996VirtualRealityAnnualInternationalSymposium
|     |     |     |     |     | in gears of | war 2. Lecture | Notes in Computer | Science |
| --- | --- | --- | --- | --- | ----------- | -------------- | ----------------- | ------- |
(VRAIS96)(Washington,DC,USA,1996),IEEECom-
| puterSociety,p.95. |     |     |     |     | (2009). |     |     |     |
| ------------------ | --- | --- | --- | --- | ------- | --- | --- | --- |
[SWP11] SCHERZERD.,WIMMERM.,PURGATHOFERW.:Asur-
[SEA08] SINTORNE.,EISEMANNE.,ASSARSSONU.:Sample-
veyofreal-timehardshadowmappingmethods.Computer
basedvisibilityforsoftshadowsusingalias-freeshadow
GraphicsForum30,1(Feb.2011),169–186.
maps.ComputerGraphicsForum(ProceedingsoftheEu-
| rographics | Symposium | on Rendering | 2008) | 27, 4 (June |                                                   |     |     |     |
| ---------- | --------- | ------------ | ----- | ----------- | ------------------------------------------------- | --- | --- | --- |
|            |           |              |       |             | [TDR*11] TEMPLINK.,DIDYKP.,RITSCHELT.,EISEMANNE., |     |     |     |
2008),1285–1292.
|     |     |     |     |     | MYSZKOWSKI | K., SEIDEL      | H.-P.: Apparent | resolution en- |
| --- | --- | --- | --- | --- | ---------- | --------------- | --------------- | -------------- |
|     |     |     |     |     | hancement  | for animations. | In Proceedings  | of the 27th    |
[SGHS98] SHADEJ.,GORTLERS.,HEL.-w.,SZELISKIR.:Lay- SpringConferenceonComputerGraphics(Vinicne,Slo-
ereddepthimages.InSIGGRAPH’98:Proceedingsofthe
vakRepublic,2011),pp.85–92.
25thAnnualConferenceonComputerGraphicsandIn-
teractiveTechniques(NewYork,NY,USA,1998),ACM, [Tek95] TEKALP A. M.: Digital Video Processing. Prentice
pp.231–242.
Hall,NewYork,NY,USA,1995.
[Shi95] SHINYAM.:ImprovementsonthePixel-tracingFil- [TM98] TOMASIC.,MANDUCHIR.:Bilateralfilteringforgray
ter:Reflection/Refraction,Shadows,andJittering.InPro- andcolorimages.InProceedingsoftheICCV(1998),pp.
| ceedings | of the Graphics | Interface | ’95 (1995), | pp. 92– | 839–846. |     |     |     |
| -------- | --------------- | --------- | ----------- | ------- | -------- | --- | --- | --- |
102.
[TV05] TAKEUCHIT.,VALOISK.D.:Sharpeningimagemo-
[SJW07] SCHERZERD.,JESCHKES.,WIMMERM.:Pixel-correct tionbasedonthespatio-temporalcharacteristicsofhuman
shadowmapswithtemporalreprojectionandshadowtest vision.InProc.SPIE,Vol.5666,690(2005),pp.83–94.
| confidence. | In Proceedings | of  | the Eurographics | Sympo- |     |     |     |     |
| ----------- | -------------- | --- | ---------------- | ------ | --- | --- | --- | --- |
siumonRendering(2007),pp.45–50. [VALBW06] VELA´ZQUEZ-ARMENDA´RIZ E., LEE E., BALA K.,
|     |     |     |     |     | WALTER B.: | Implementing | the render | cache and the |
| --- | --- | --- | --- | --- | ---------- | ------------ | ---------- | ------------- |
[SKUT*10] SZIRMAY-KALOS L., UMENHOFFER T., TOTH B., edge-and-point image on graphics hardware. In GI ’06:
|            |           |            |                   |     | Proceedings | of Graphics | Interface 2006 | (Toronto, ON, |
| ---------- | --------- | ---------- | ----------------- | --- | ----------- | ----------- | -------------- | ------------- |
| SZECSI L., | SBERT M.: | Volumetric | ambient occlusion | for |             |             |                |               |
real-timerenderingandgames.IEEEComputerGraphics Canada,2006),CanadianInformationProcessingSociety,
| andApplications30(2010),70–79. |     |     |     |     | pp.211–217. |     |     |     |
| ------------------------------ | --- | --- | --- | --- | ----------- | --- | --- | --- |
[SLS*96] SHADE J., LISCHINSKI D., SALESIN D. H., DEROSE [WBB*07] WAND M., BERNER A., BOKELOH M., FLECK
T.,SNYDERJ.:Hierarchicalimagecachingforaccelerated A., HOFFMANN M., JENKE P., MAIER B., STANEKER D.,
walkthroughs of complex environments. In SIGGRAPH SCHILLING A.: Interactive editing of large point clouds.
InProceedingsoftheSymposiumonPoint-BasedGraph-
’96:Proceedingsofthe23rdAnnualConferenceonCom-
puter Graphics and Interactive Techniques (New York, ics 2007 : Eurographics/IEEE VGTC Symposium Pro-
NY,USA,1996),ACM,pp.75–82. ceedings (Prague, Czech Republik, 2007), B. Chen,
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.

2408 Scherzeretal./TemporalCoherenceMethodsinReal-TimeRendering
M. Zwicker, M. Botsch and R. Pajarola R. (Eds.), Eu- [WSP04] WIMMERM.,SCHERZERD.,PURGATHOFERW.:Light
rographicsAssociation,pp.37–46. space perspective shadow maps. In Rendering Tech-
|         |                                        |     |     |     |     | niques 2004 | (Proceedings |       | of the Eurographics |        | Sympo-    |
| ------- | -------------------------------------- | --- | --- | --- | --- | ----------- | ------------ | ----- | ------------------- | ------ | --------- |
| [WDG02] | WALTERB.,DRETTAKISG.,GREENBERGD.P.:En- |     |     |     |     |             |              |       |                     |        |           |
|         |                                        |     |     |     |     | sium on     | Rendering)   | (June | 2004), A.           | Keller | and H. W. |
hancingandoptimizingtherendercache.InEGRW’02: Jensen (Eds.), Eurographics, Eurographics Association,
| Proceedingsofthe13thEurographicsWorkshoponRen- |     |                     |     |                     |     | pp.143–151. |     |     |     |     |     |
| ---------------------------------------------- | --- | ------------------- | --- | ------------------- | --- | ----------- | --- | --- | --- | --- | --- |
| dering (Aire-la                                |     | Ville, Switzerland, |     | 2002), Eurographics |     |             |     |     |     |     |     |
Association,pp.37–42. [XV96] XIA J. C., VARSHNEY A.: Dynamic view-
dependentsimplificationforpolygonalmodels.InIEEE
[WDP99] WALTERB.,DRETTAKISG.,PARKERS.:Interactive
|     |     |     |     |     |     | Visualization | ’96 | (1996), | R. Yagel and | G.  | M. Nielson |
| --- | --- | --- | --- | --- | --- | ------------- | --- | ------- | ------------ | --- | ---------- |
renderingusingtherendercache.InRenderingtechniques
(Eds.),pp.335–344.
’99(Proceedingsofthe10thEurographicsWorkshopon
Rendering)(NewYork,NY,USA,Jun1999),D.Lischin- [YNS*09] YANG L., NEHAB D., SANDER P. V., SITTHI-
skiandG.Larson(Eds.),vol.10,Springer-Verlag/Wien, P., LAWRENCE J., HOPPE H.: Amortized super-
AMORN
pp.235–246. sampling. ACM Transactions on Graphics 28, 5 (2009),
135.
[WDS04] WALDI.,DIETRICHA.,SLUSALLEKP.:Aninterac-
tiveout-of-corerenderingframeworkforvisualizingmas-
|     |     |     |     |     |     | [YSL08] YANG | L., | SANDER | P. V., LAWRENCE | J.: | Geometry- |
| --- | --- | --- | --- | --- | --- | ------------ | --- | ------ | --------------- | --- | --------- |
sivelycomplexmodels.InProceedingsoftheEurograph-
awareframebufferlevelofdetail.ComputerGraphicsFo-
| icsSymposiumonRendering(2004). |     |     |     |     |     | rum27,4(2008),1183–1188. |     |     |     |     |     |
| ------------------------------ | --- | --- | --- | --- | --- | ------------------------ | --- | --- | --- | --- | --- |
[WGS99] WIMMER M., GIEGL M., SCHMALSTIEG D.: Fast [YTS*11] YANGL.,TSEY.-C.,SANDERP. V.,LAWRENCEJ.,
walkthroughswithimagecachesandraycasting.InVir- NEHABD.,HOPPEH.,WILKINSC.L.:Image-basedbidirec-
tualEnvironments’99:Proceedingsofthe5thEurograph-
tionalscenereprojection.ACMTransactionsonGraphics
| ics Workshop | on  | Virtual Environments |     | (June 1999), | M.  |     |     |     |     |     |     |
| ------------ | --- | -------------------- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- |
30,6(2011),150.
Gervautz,D.Schmalstieg.,andA.Hildebrand(Eds.),Eu-
rographics, Springer-Verlag Wien, pp. 73–84. (ISBN 3- [YWY10] YUX.,WANGR.,YUJ.:Real-timedepthoffield
211-83347-1) renderingviadynamiclightfieldgenerationandfiltering.
ComputerGraphicsForum(Proc.ofPacificGraphics)29,
| [WKC94]     | WALLACH | D. S.,      | KUNAPALLI | S., COHEN  | M. F.:  | 7(2010). |     |     |     |     |     |
| ----------- | ------- | ----------- | --------- | ---------- | ------- | -------- | --- | --- | --- | --- | --- |
| Accelerated | MPEG    | compression |           | of dynamic | polygo- |          |     |     |     |     |     |
nal scenes. In Proceedings of SIGGRAPH (1994), pp. [ZMHI97] ZHANGH.,MANOCHAD.,HUDSONT.,HOFFIIIK.
193–197. E.: Visibility culling using hierarchical occlusion maps.
InProceedingsofSIGGRAPH(1997),pp.77–88.
| [WS99] WARD | G., | SIMMONS | M.: The | holodeck ray | cache: |                                                |     |     |     |     |     |
| ----------- | --- | ------- | ------- | ------------ | ------ | ---------------------------------------------- | --- | --- | --- | --- | --- |
|             |     |         |         |              |        | [ZWL05] ZHUT.,WANGR.,LUEBKED.:Agpu-accelerated |     |     |     |     |     |
Aninteractiverenderingsystemforglobalilluminationin
nondiffuseenvironments.ACMTransactionsonGraphics render cache. Pacific Graphics (Short Paper Session)
| 18,4(1999),361–368. |     |     |     |     |     | (October2005). |     |     |     |     |     |
| ------------------- | --- | --- | --- | --- | --- | -------------- | --- | --- | --- | --- | --- |
(cid:2)c 2012TheAuthors
ComputerGraphicsForum(cid:2)c 2012TheEurographicsAssociationandBlackwellPublishingLtd.
