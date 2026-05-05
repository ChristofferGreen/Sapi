# 04-foveated-rendering-a-state-of-the-art-survey

Computational Visual Media
 https://doi.org/10.1007/s41095-022-0306-4                                   Vol. 9, No. 2, June 2023, 195–228

 Review Article



Foveated rendering: A state-of-the-art survey

Lili Wang1,2,3 , Xuehuai Shi1 (        ), and Yi Liu1

c The Author(s) 2022.


Abstract Recently, virtual reality (VR) technology             survey will provide new researchers with a high-level
has been widely used in medical, military, manufac-            overview of the state-of-the-art in this field, furnish
turing, entertainment, and other fields. These app-            experts with up-to-date information, and offer ideas
lications must simulate different complex material             alongside a framework to VR display software and
surfaces, various dynamic objects, and complex                 hardware designers and engineers.
physical phenomena, increasing the complexity of VR            Keywords foveated rendering; virtual reality (VR);
scenes. Current computing devices cannot efficiently                    real-time rendering
render these complex scenes in real time, and
delayed rendering makes the content observed by
the user inconsistent with the user’s interaction,             1    Introduction
causing discomfort. Foveated rendering is a promising
                                                               In recent years, virtual reality (VR) technology
technique that can accelerate rendering. It takes
                                                               has been widely used in medical [1–3], military
advantage of human eyes’ inherent features and
                                                               [4–6], manufacturing [7–9], entertainment [10–12],
renders different regions with different qualities without
                                                               and other fields [13–15]. Despite the increasing
sacrificing perceived visual quality. Foveated rendering
research has a history of 31 years and is mainly focused
                                                               computational power of devices, rendering overhead
on solving the following three problems. The first             continues to increase owing to the diversification of
is to apply perceptual models of the human visual              surface materials of virtual objects, the increasing
system into foveated rendering. The second is to               number of dynamic objects, and the higher complexity
render the image with different qualities according            of physical phenomena to be simulated in VR
to foveation principles. The third is to integrate             applications. Moreover, Potter et al. [16] demon-
foveated rendering into existing rendering paradigms           strated that the visual latency tolerance threshold
to improve rendering performance. In this survey, we           for the human visual system (HVS) is approximately
review foveated rendering research from 1990 to 2021.          13 ms [16], making it more difficult for these applications
We first revisit the visual perceptual models related          to meet HVS real-time requirements. If rendering
to foveated rendering. Subsequently, we propose a              results are too delayed, users will observe that the
new foveated rendering taxonomy and then classify              content is inconsistent with the interaction, which
and review the research on this basis. Finally, we             creates discomfort. Therefore, improving rendering
discuss potential opportunities and open questions in          performance is a critical factor in promoting the
the foveated rendering field. We anticipate that this          practicality of VR technology.
                                                                 Foveated rendering is an accelerated rendering
1 State Key Laboratory of Virtual Reality Technology           technology that allocates computing resources based
  and Systems, Beihang University, Beijing 100000,             on HVS perceptual models. More computing resources
  China.    E-mail: L. Wang, wanglily@buaa.edu.cn;             are allocated to the fovea of human eyes, while
  X. Shi, shixuehuaireal@buaa.edu.cn ( ), Y. Liu,
                                                               fewer are allocated to the periphery. The fovea
  song1997@buaa.edu.cn.
2 Peng Cheng Laboratory, Shengzhen 518000, China.
                                                               is responsible for clear central vision because
3 Beijing Advanced Innovation Center for Biomedical            approximately half of the optic nerve fibers are
  Engineering, Beihang University, Beijing 100000, China.      distributed in the fovea of the retina, and the
Manuscript received: 2021-12-21; accepted: 2022-07-29          remaining half is distributed to the rest of the

                                                         195

196                                                                                       L. Wang, X. Shi, Y. Liu


periphery [17]. Foveated rendering takes advantage            resolutions of the HVS and high-quality rendering
of this inherent feature of human eyes. It performs           in regions with high spatial resolutions to improve
different rendering qualities in different regions of         rendering performance without perceptual loss.
the image. High-quality rendering is performed in             The contrast sensitivity models describe the
the foveal region (fovea), and low-quality rendering          relationship between different contrast levels and
is performed in the peripheral region (periphery).            the sensitivity of the HVS. The application
Therefore, foveated rendering can speed up rendering          of foveated rendering mainly includes various
without sacrificing perceived visual quality.                 contrast sensitivity functions (CSFs), such as
   Three challenges must be addressed in foveated             the spatial CSF, spatio-temporal CSF, spatio-
rendering: the first is to use the perceptual model           luminance CSF, spatio-chromatic CSF, and
of the human visual system to guide foveated                  critical flicker fusion. According to the contrast
rendering, the second is to render different regions          sensitivity model, foveated rendering can allocate
with different qualities, and the third is to integrate       less computational resources to the regions with
foveated rendering into existing rendering paradigms          low contrast sensitivity to improve rendering
to improve rendering performance.                             performance without losing visual perception.
• Using the perceptual model of the human                 •   Rendering different regions with different
    visual system to guide foveated rendering.                qualities. Foveation principles should be
    This reduces computational overhead and ensures           considered to address this challenge. Level of
    the user does not experience quality loss from the        detail (LoD) techniques in computer graphics
    images generated. The basic idea of foveated              provide a solution to render 3D scenes composed
    rendering is to render the results of different           of geometric meshes with different qualities.
    qualities to different regions to accelerate the          This increases rendering efficiency by decreasing
    rendering process; therefore, it is first necessary       geometric mesh complexity and maintaining
    to evaluate the rendering result quality based            unnoticed visual quality reduction. LoD tech-
    on the HVS. A well-designed questionnaire for             niques select different levels of details according
    user studies is a straightforward approach to             to the viewpoint position and orientation. When
    evaluate the visual quality of rendering results.         using LoD technology to render geometric meshes
    However, this requires many user experiments              by foveated rendering [19, 20], the user’s fovea
    to obtain effective results, which is extremely           is detected first, then the meshes that must
    time-consuming. Prior to conducting large-                be tessellated according to the fovea are finely
    scale user studies, researchers frequently use            controlled, and finally refined meshes are used
    perceptual models and related metrics to evaluate         to generate high-quality rendering results in the
    the visual quality of rendering results and then          foveal region. LoD technology is not only suitable
    perform user evaluations based on the results             for geometric meshes but also for other data
    with satisfactory quality, thereby improving              representations, such as point cloud data [21].
    evaluation efficiency. Visual quality is related          In addition to the degree of mesh tessellation,
    to perceptual sensitivity [18]. The two most              the rendering sampling rate in rendering is
    representative perceptual models related to the           also an essential factor that directly affects the
    foveated rendering technique are the visual               quality of the resulting image. User behavior
    acuity and contrast sensitivity models. The               and performance have been evaluated in user
    visual acuity models describe the relationship            studies [18, 22, 23]. The results showed that
    between different regions in the visual field             users could not distinguish images with a reduced
    and the spatial resolution of the HVS. When               sampling rate below the perceptual thresholds in
    applied to foveated rendering, the visual acuity          the peripheral regions from full resolution images.
    models can be divided into the fall-off, binocular        Multi-spatial resolutions based foveated rendering
    horopter, and ocular dominance models. Based              methods perform high-resolution sampling for
    on these models, foveated rendering allows low-           foveal regions and some important regions that
    quality rendering in regions with low spatial             users may notice, and low-resolution sampling

Foveated rendering: A state-of-the-art survey                                                                  197


    for peripheral regions. Alongside the concept of       method taxonomies and classifies previous methods.
    multi-spatial resolution, multi-temporal, multi-       Section 4 revisits early related foveated rendering
    luminance, and multi-color resolution can also         research from 1990 to 2011 based on the taxonomy.
    be used to accelerate foveated rendering. In this      Section 5 reviews methods that emerged over the past
    survey, these foveation principles are essential       decade based on the taxonomy. Research conducted
    factors in our taxonomy of foveated rendering          in the first 20 years and the last 10 years are separated
    technologies.                                          because the focus of foveated rendering research
• Integrating foveated rendering into exis-                has changed. Finally, Section 6 discusses foveated
    ting rendering paradigms to improve                    rendering open questions and opportunities.
    rendering performance. Rasterization is the
    most widely studied rendering paradigm in              2     Applying visual perceptual models in
    foveated rendering [24, 25]. To rasterize the
                                                                 foveated rendering
    image with different resolutions in screen space,
    early research first rasterized the full resolution    First, the HVS visual features involved in foveated
    image and then reduced the image resolution in         rendering are briefly summarized. Then, perceptual
    the desired region with time-consuming filters,        models are introduced after which we discuss the
    which opposed the goal of foveated rendering.          application of these models in foveated rendering.
    Since 2012, foveated rendering using rasterization     We recommend Weier et al.’s survey [39] to those who
    has only performed high-resolution rendering in        wish to establish a more comprehensive understanding
    foveal regions and some important regions that         of perception-based rendering techniques.
    users may notice, and low-resolution rendering in      2.1     HVS features       involved     in    foveated
    peripheral regions [26–30]. Because implementing               rendering
    rasterization into foveated rendering may create
    multiple rendering passes, a general rendering         Currently, HVS primary visual features involved in
    pipeline to rasterize pixels with foveated rendering   foveated rendering include visual acuity and contrast
    in a single render pass was introduced, thereby        sensitivity. Both are described as follows.
    further improving rendering efficiency [23]. The       2.1.1   Visual acuity
    ray tracing rendering paradigm can control the         Visual acuity refers to the ability to discern shapes
    number of rays emitted by each pixel. This             and details of objects [40]. As the main HVS feature
    directly supports the multi-spatial resolution.        widely used in foveated rendering, it has the following
    Therefore, many researchers implemented this           properties:
    approach with foveated rendering [31–34].              • Foveal \peripheral vision. Human visual acuity is
    Besides rasterization and ray tracing, some               not uniform over the whole visual field. When a
    studies focus on implementing other rendering             person looks at an object, the foveal vision scene
    paradigms into foveated rendering, such as ray            details can be recognized; however, the peripheral
    casting, instant radiosity, and neural rendering          vision scene cannot be clearly recognized [43].
    [35–38]. Hence, the rendering paradigm is also            That is, the HVS has higher visual acuity in
    an essential factor in our taxonomy.                      the fovea of the human visual region and is the
  This survey aims to review the state-of-the-art             basis of foveated rendering. Figure 1(a) shows
in the field of foveated rendering, and to discuss            a schematic illustration of the foveal\peripheral
foveated rendering methods with different input data          vision.
types, foveation principles, and rendering paradigms       • Fusional vision. The movement of both eyes
in design and implementation, especially 3D foveated          enables the fusion of monocular images producing
rendering methods that emerged in the past 10 years.          binocular vision. In fusional vision, the area
  This section briefly introduces foveated rendering          where objects are perceived as single unified
concepts and challenges. Section 2 discusses the              objects when viewed with both eyes is called
application of HVS perceptual models to foveated              Panum’s fusional area [44]. The scene out of
rendering. Section 3 proposes foveated rendering              the Panum’s fusional area is recognized as a

198                                                                                                                   L. Wang, X. Shi, Y. Liu




Fig. 1 (a) Schematic illustration of foveal\peripheral vision from Ivančić Valenko et al. [41]. The eccentric angle of the foveal region is very
small, while the eccentric angle of the parafoveal region is up to 10◦ . The eccentric angle of the near peripheral region is about 60◦ and that of
the peripheral region area is 180◦ . (b) Schematic illustration of fusional vision from Schaadt [42]. Two laterally placed eyes provide us two
horizontally shifted and disparate images of the visual scene, which are continuously integrated into a single percept. (c) Schematic illustration
of dominant eye. Compared with the nondominant eye, the dominant eye contributes more to the binocular vision. Reproduced with permission
from Ref. [41], c Portal hrvatskih znanstvenih i stručnih čsopisa–Hrčak 2019; Ref. [42], c Universität des Saarlandes 2015.


  “double image” with lower image quality and less                               velocity to improve foveated rendering quality
  visual realism [45]. It can be used to simplify the                            and performance.
   scene out of Panum’s fusional area for efficient                        •     Spatio-luminance contrast sensitivity. This refers
   foveated rendering. Figure 1(b) shows a schematic                             to the HVS spatial contrast sensitivity at
   illustration of fusional vision.                                              different luminances. Adjusting rendering quality
• Dominant eye. Both eyes have different sen-                                    according this aspect in environments with
   sitivity to visual stimuli in the HVS, i.e., one                              different luminances can also improve foveated
   is more sensitive than the other, and the eye                                 rendering quality and performance.
  with higher sensitivity is called the dominant                           •     Spatio-chromatic contrast sensitivity. This refers
   eye [46]. Less computational resources can be                                 to the HVS contrast sensitivity through grating
   allocated for the non-dominant eye to speed up                                stimulation with sinusoidally changing colors [50].
   rendering when performing foveated rendering                                  In particular environments, such as bars, fog,
   for binoculars. Figure 1(c) shows a schematic                                 and other scenes with prominent theme colors,
   illustration of the dominant eye.                                             foveated rendering can also use this aspect to
2.1.2    Contrast sensitivity                                                    improve perceptual quality.
Contrast sensitivity refers to the ability to distinguish                  2.2     Perceptual models and foveated ren-
between foreground objects and background [47].                                    dering applications
This varies from individual to individual, reaching
a maximum at approximately the age of 20, and                              Based on the HVS features, perceptual models
subsequently decreases with age. Other factors (such                       were proposed and used in foveated rendering to
as cataracts and diabetic retinopathy) can also cause                      approximate the HVS functions and features through
a decrease in contrast sensitivity. Contrast sensitivity                   mathematical descriptions. These models could
can be considered from the following distinct aspects:                     guide foveated rendering design and determine the
• Spatial contrast sensitivity. This refers to the                         perceptual quality of the rendering result. This
    HVS sensitivity in recognizing patterns at                             section reviews the perceptual models, and their
    different frequencies [48]. For certain scene regions                  application in foveated rendering based on the HVS
    to be rendered, where the HVS frequency is less                        features discussed.
    sensitive, it is possible to perform lower quality                     2.2.1     Visual acuity models
    rendering in these regions to improve efficiency.                      Visual acuity models describe the function of visual
• Spatio-temporal contrast sensitivity. This refers to                     acuity with neural and optical factors. Various
    the HVS spatial contrast sensitivity at different                      visual acuity models have been developed based
    retinal velocities [49]. Rendering quality can                         on foveal/peripheral vision, fusional vision, and
    be dynamically adjusted to the current retinal                         dominant eye.

Foveated rendering: A state-of-the-art survey                                                                                199


   Visual acuity fall-off model. This is the psycho-                       algorithms with the visual acuity fall-off model to
physical model that shows the degradation behavior                         dynamically adjust the number of vertices extracted
of visual acuity with eccentricity [53]. Weymouth [54]                     based on the visual sensitivity corresponding to each
demonstrated that acuity could be measured in                              pixel to achieve LoD, i.e., higher accuracy for face
terms of MAR (minimum angular resolution). A                               slices in the gaze point region and lower accuracy for
linear model matches both anatomical data and                              face slices in the surrounding region [19, 58–60]. The
performance results on many vision tasks. Daniel and                       behavioral performance cost of a series of perceptual
Whitteridge [55] proposed the cortical magnification                       experimental surface gaze level-of-detail techniques
factor (CMF), which provides the mapping from the                          can be offset by the behavioral performance gain from
visual angle to a cortical diameter in millimeters.                        increased rendering speed. In more recent research
The magnification factor is the largest in 0◦ –20◦ and                     on the topic, Guenter et al. [26] simulated the acuity
decreases with eccentricity for the periphery. Levi                        drop by rendering three nested layers of increasing
et al. [56] stated that MAR increases linearly with                        angular diameters and decreasing resolution around
eccentricity in the first 20◦ –30◦ . The higher the                        the gaze direction. These layers were fused into the
eccentricity, the faster the angular dimension rises.                      final result image. This work employed the CMF
From the center of the visual vision to the peripheral                     to decrease resolution, achieved significant shading
vision, the spatial sensitivity is reduced by 35× [57].                    reductions, and introduced overhead by repeating
Figure 2 shows an example of the visual acuity fall-off                    rasterization. Vaidyanathan et al. [61] proposed an
model from Geisler and Perry [51].                                         architecture for the flexible control of shading rates
   In early foveated rendering research, Levoy and                         in a GPU pipeline and tested their architecture for
Whitaker [35] combined the ray casting method used                         foveated rendering with a simplified visual acuity
for volume rendering with the visual acuity fall-off                       fall-off model. Weier et al. [62] combined the visual
model. For each pixel on the image plane, they                             acuity fall-off model with the re-projection technique
first calculated the eccentricity of the pixel, then                       and applied it in the ray tracing algorithm for head
obtained the visual acuity of this pixel based on the                      mounted displays (HMDs). For each frame, if the
eccentricity and the visual acuity fall-off model, and                     re-projection technique cannot reuse the rendering
finally modulated the number of rays casting on this                       result of the previous frame, the number of sampling
pixel and the number of samples per unit length of                         rays required for the current pixel is determined by
each ray based on acuity to generate the rendering                         the corresponding visual acuity, with higher visual
result. Some studies combined vertex decimation                            acuity requiring a larger number of sampling rays
                                                                           and lower visual acuity requiring a smaller number.
                                                                              Binocular horopter Model. An empirical binocular
                                                                           horopter model was introduced by Panum [64], which
                                                                           reported that the sensory mechanism of the HVS
                                                                           fuses the images perceived by two eyes. This fusion
                                                                           leads to a single vision experience in the average
                                                                           visual direction and Panum’s fusional area, as shown
                                                                           in Fig. 3. Mitchell [65] measured the upper limit of
                                                                           the parallax range, which was used to represent the
                                                                           upper disparity tolerance of the sensory mechanism
                                                                           for fusion.
                                                                              In foveated rendering, Ohshima et al. [58] used
                                                                           fusion vision theory to control the geometric meshes
Fig. 2 Visual acuity fall-off model proposed by Geisler and Perry [51].    level of detail. They reduced the complexity of
The HVS visual acuity is the largest (40 cpd) when the eccentricity        geometry out of the fusional area to accelerate
angle is 0◦ . With the increase of eccentricity, visual acuity decreases
                                                                           rendering. Based on the theory of fusion vision, many
linearly. When the eccentricity angle exceeds 45◦ , visual acuity
decreases to 0 cpd. “cpd” means cycles per degree. Reproduced              other studies focus on improving the depth-of-field
with permission from Ref. [52], c ACM 2021.                                blur effects [24, 66–72].

200                                                                                                                     L. Wang, X. Shi, Y. Liu


                                                                             2.2.2     Contrast sensitivity models
                                                                             In foveated rendering, contrast sensitivity models
                                                                             mainly describe the HVS ability to distinguish objects
                                                                             from the background behind objects at different
                                                                             spatial frequencies [76], such as contrast sensitivity
                                                                             functions (CSFs); and the threshold at which an
                                                                             identical flickering stimulus varies in percept from
                                                                             flickering to stable, such as critical flicker fusions
                                                                             (CFFs). In CSF research, attention is paid not
                                                                             only to the influence of the most fundamental
                                                                             spatial frequencies, but also the influence of temporal
                                                                             frequencies, luminances, and colors [52, 77, 78]. In
                                                                             CFF research, attention is focused on measuring the
                                                                             threshold at which the HVS can perceive the stable
Fig. 3 Panum’s fusional area: objects within the area are perceived as
single images, objects further away are seen perceived with uncrossed        flickering stimulus in the temporal domain [52, 79].
disparity, and the objects closer to the viewer with crossed disparity.         Spatial CSF. This was first proposed by Schade [84]
Reproduced with permission from Ref. [63], c ACM 2010.
                                                                             and measured the contrast detection threshold of the
                                                                             most sensitive part of the range in a logarithmic scale
   Ocular dominance model. The ocular dominance                              range, and distributed evenly on the most sensitive
model was proposed by Porac and Coren [46], which                            part of this range, typically 1–16 cpd. Nowadays, the
showed that the HVS tends to use one eye instead of                          most commonly used spatial CSF is the threshold
both to perceive the scene. Shneor and Hochstein [73]                        set measured by Watson [80] as a function of spatial
evaluated the effect of ocular dominance under non-                          frequency. Examples in Fig. 4(a) show that spatial
rivalry conditions and concluded that the dominant                           CSF peaks between 4 and 5 cpd and falls rapidly at
eye has priority in visual processing and may inhibit                        higher frequencies.
the performance of the non-dominant eye. Koçtekin                              In early foveated rendering research, many
et al. [74] evaluated the performance of the dominant                        researchers used spatial CSF to accelerate rendering
eye for color vision discrimination ability among                            by reducing the geometry complexity of the scene
medical students with normal color vision and                                in the high static spatial frequency region [85–87].
concluded that the dominant eye takes priority in                            Because the HVS is less sensitive to high-frequency
the r/g color spectral region, probably including                            patterns in the peripheral regions, the HVS can
inhibition of the non-dominant eye.                                          tolerate greater errors in the high-frequency regions
   Meng et al. [75] adopted the ocular dominance                             of the rendered scene. Recently, Patney et al. [88]
model into foveated rendering and rendered the non-                          introduced a novel anti-aliasing algorithm to help
dominant display with a more aggressive foveation to                         recover peripheral details that are resolvable by
accelerate foveated rendering on HMDs.                                       our eyes. This algorithm provides details that the




Fig. 4 CSFs over the range of spatial frequencies, temporal frequencies, luminances, and colors. (a) Spatial CSF with the measured data from
Watson [80]. (b) Spatio-temporal CSF derived from sensitivity measurements in Yee et al. [81], where v is the velocities of the retinal images
that measured in d/s. (c) Spatio-luminance CSF measured by Barten’s model in Westland et al. [82] for stimulus of size 10 cpd and mean
luminance 50 (thin solid line), 25 (dashed line), 2.5 (dotted line), 0.25 (dashdotted line), and 0.025 (thick solid line) cd/m2 . (d) Spatio-chromatic
CSF for black–white, red–green, and yellow–blue contrast from Fairchild [83]. Reproduced with permission from Ref. [80], c Optical Society of
America 2000; Ref. [81], c ACM 2001; Ref. [82], c Wiley Periodicals, Inc. 2006; Ref. [83], c John Wiley and Sons 2013.

Foveated rendering: A state-of-the-art survey                                                                  201


periphery of the HVS can perceive. Koskela et al. [31]      such that the number of colored samples is further
demonstrated that the smallest detail that humans           distributed in the image with essential features.
can resolve is 60 cpd on average. If a rendering system     Tursun et al. [29] proposed a new luminance-contrast-
could be built capable of showing 60 cpd, 95% of the        aware foveated rendering technique, which analyzed
rendered detail would be excessive. Then Koskela            the local luminance contrast of the image to obtain
et al. [33] proposed a novel Visual-Polar coordinate        a particular foveation to improve computational
space and distributed the samples according to the          savings.
spatial CSF in the Visual-Polar coordinate space.              Spatio-chromatic CSF. The HVS contrast sensi-
   Spatio-temporal CSF. The HVS contrast sensitivity        tivity changes significantly with sinusoidally changing
not only changes with spatial frequency but also with       colors at the same spatial frequency. Mullen [92]
retinal velocities. The spatio-temporal CSF measures        performed experiments that compare the decline
the HVS contrast sensitivity with spatial frequency         in contrast sensitivity between the color-only (red–
and retinal-image motion. Kelly [49] measured the           green) gratings and the monochromatic luminance
CSF by allowing the user to observe sine waves with         gratings in the entire field of view when the spatial
different retinal velocities. Contrast sensitivity varies   frequency is 2 cpd, at the center of the fovea and the
significantly with retinal velocity. Liu and Jiang [89]     eccentricity are 10◦ and 18◦ respectively. Anderson
and Flipse et al. [90] reported that if the velocity of     et al. [93] measured the CSF for eccentricities from
the retinal image is identical, the contrast sensitivity    0◦ to 55◦ for chromatic red–green sinusoidal stimuli
of the eye during fixation and pursuit will be equal,       and reported that chromatic contrast declines more
i.e., the motion of the retinal image, not the motion of    steeply than luminance contrast with eccentricity.
the eye, determines contrast sensitivity. Figure 4(b)       Mullen and Kingdom [94] measured the cone contrast
shows that the temporal CSF varies with different           sensitivities for sine-wave grating stimuli (smoothly
velocities of the retinal images.                           enveloped in space and time) for two colors (red–green
   In foveated rendering, Yee et al. [81] constructed a     and blue–yellow) and monochromatic luminance at
spatio-temporal error tolerance map based on a spatio-      a range of eccentricities in the nasal field (0◦ –25◦ ).
temporal CSF to accelerate rendering and achieved a         They identified that red–green cone opponency has a
significant improvement in speed. Stengel et al. [28]       steep decline away from the fovea, while the loss in
introduced a sampling scheme combined with a spatio-        blue–yellow cone opponency is more gradual, showing
temporal CSF, which performs shading on regions of          a similar loss to that found for achromatic vision.
essential features in the image, and interpolates the       Mullen et al. [95] measured the cone contrast for red–
remaining regions, to avoid affecting user perceived        green and blue–yellow colors. The results showed that
quality.                                                    red–green cone opponency declines steeply across the
   Spatio-luminance CSF. The HVS contrast sensi-            human periphery and becomes behaviorally absent
tivity changes with luminance under the same spatial        by 25◦ –30◦ . Chwesiuk and Mantiuk [78] reported
frequency. Van Meeteren and Vos [91] measured               that the color directions closer to the chromatic
contrast sensitivity with a luminance ranging from          green-to-red axis show higher contrast sensitivity
0.0001 to 10 cd/m2 in the case of a spatial frequency       in comparison with achromatic stimuli, while for
ranging from 0.5 to 30 cpd. Kim et al. [77] extended        the yellow-to-blue axis, the sensitivity is lower.
the contrast sensitivity measure into higher luminance      Figure 4(d) shows that the color CSF varies with
levels (150 cd/m2 ) with lower spatial frequencies,         black–white, red–green, and yellow–blue.
down to 0.125 cpd. Higher luminance levels are more            Duchowski and Çöltekin [96] introduced the
relevant to photopic vision, and low frequencies are        possibility of developing a perceptually-based color
required to observe and model the CSF band-pass             degradation metric, which can be used to accelerate
characteristic, especially for low luminance levels.        foveated rendering. They also investigated the
Figure 4(c) shows that the luminance CSF varies             peripheral color reduction with the color CSF; the
with different mean luminances.                             results suggested that peripheral chromaticity cannot
   In foveated rendering, Stengel et al. [28] proposed      be reduced within the central 20◦ visual angle.
a luminance map to adjust the sampling probability             Critical flicker fusion. Besides CSFs that focus

202                                                                                                    L. Wang, X. Shi, Y. Liu


on distinguishing objects from the background,              from the center of gaze increases.
researchers measured the threshold at which an                 In the resolution classification, the foveated
identical flickering stimulus varies in percept from        display can be divided into four categories according
flickering to stable, i.e., critical flicker fusion (CFF)   to the relationship between the visual acuity
[52, 79]. Tyler and Hamer [79] introduced the Ferry–        distribution function (ADF) and the display reso-
Porter law considering spatio-temporal frequency            lution distribution function (RDF) (Fig. 5). Class
and luminance, which described that CFF increases           A is acuity matched. This is a conservative display
linearly with log retinal luminance and log stimulus        method. The display resolution used in the foveal
area, respectively. Tyler and Hamer [97] showed             and peripheral region is higher than the perceptible
that the Ferry–Porter law also extends to higher            resolution threshold in the visual acuity distribution
eccentricities. Krajancich et al. [52] introduced           function. This type of method ensures the user does
a model to measure the eccentricity-dependent               not perceive the resolution drop. Class B is fovea
critical flicker fusion thresholds for space, time,         matched, which means that the display resolution is
and luminance. This showed that the CFF varies              higher than the user’s perceptible threshold in the
with spatial frequency and luminance and exhibited          foveal region. In contrast, the display resolution is
an anti-foveated effect, with the highest thresholds        lower than the user’s perceptible threshold in the
observed in the near–mid periphery of the visual field.     peripheral region. To further improve efficiency,
Although no research directly applied the eccentricity-     this type of method only focuses on the quality of
based CFF to foveated rendering algorithms, this            the foveal region. Class C is periphery matched,
provided a new model to improve foveated rendering          i.e., the user does not perceive any artifacts in the
efficiency.                                                 peripheral region; however, the display resolution
                                                            in the foveal region fails to meet or exceed user
3     3D foveated rendering taxonomies                      visual acuity. Class D is non-acuity matched, which
                                                            means that in the foveal and peripheral region, the
Recent surveys proposed several taxonomies to               display resolution has not reached or exceeded the
classify existing foveated rendering techniques. In         resolution threshold that can be perceived by human
Weier et al.’s survey [39], the authors referred to         visual acuity. In using this type of method, the
foveated rendering methods as measurement-based             user is aware of artifacts in both regions. In the
perceptual approaches and classified them into two          second dimension, the gaze-contingent classification,
catalogs: one based on scene simplification, the other      the foveated display can also be divided into four
based on adaptive sampling. The methods in the first        classes according to the gaze direction range in the
catalog are object-space methods. They use geometry
techniques, such as LoD, to significantly reduce the
scene’s complexity using the visual acuity model or
CSF according to the user’s gaze position, thereby
significantly improving time performance. The
methods in the adaptive sampling class adaptively
calculate the sampling rate in rendering paradigms,
such as rasterization or ray tracing based on the visual
acuity model or CSF.
   Spjut et al. [98] proposed a two-dimensional taxo-
nomy matrix of the foveated display. The first
dimension is a resolution-contingent classification,
and the second is a gaze-contingent classification.
Resolution-contingent classification is based on the
acuity distribution function of the human visual
model. It describes how the non-linear fitting in which
                                                            Fig. 5      Four possible comparisons of the user’s visual acuity
the angular resolution perceived by the user decreases      distribution function and the display’s resolution distribution function.
as the gaze eccentricity or the angular displacement        Reproduced with permission from Ref. [98], c IEEE 2020.

Foveated rendering: A state-of-the-art survey                                                                                                   203


display. Class 1 is the fully foveated display, in which                   (2) foveation principle; (3) rendering paradigm.
the gaze direction can be any direction in the display.                    Table 2 shows the elements in each dimension.
Class 2 is the practically foveated display in which the                      Foveated rendering works for different input
gaze direction should be within ±15◦ from the center                       data. Before understanding or designing a foveated
of the display. Class 3 is the partially foveated display                  rendering method, it is necessary to consider the
in which the gaze direction should be much smaller                         processed data type. The input data type is taken
than ±15◦ . Class 4 is the non-foveated display in                         as the first dimension of our foveated rendering
which the single gaze direction is supported. Table 1                      taxonomy. Present foveated rendering methods can
summarizes the relationship between resolution and                         process the data types: image/video, volume data,
gaze-contingent classifications, and provides further                      geometric meshes, point cloud, hologram data, and
detailed descriptions for each.                                            light field.
   Weier et al. [39] provided an overview of the HVS                          The foveation principle is used as the second
perceptual mechanisms and classified existing                              dimension to classify the previous methods. Foveated
rendering techniques according to different perceptual                     rendering provides high-quality rendering for the
mechanisms. Spjut et al. [98] focused on the cla-                          HVS fovea and provides unnoticeably lower-quality
ssification of display effects, which is suitable for                      rendering for the periphery. Its core principle is multi-
hardware display devices and measures the degree of                        resolution rendering. The present methods use one or
support for foveated rendering by display devices.                         several different types of multi-resolution rendering
   The proposed taxonomy focuses on enabling                               under this ideology, including multi-spatial, multi-
researchers to easily understand the actual functions,                     temporal, multi-luminance, multi-color, and multi
basic ideas, technical framework of current methods                        geometry resolution, which is typically referred to as
and the fundamental design factors that support                            the LoD.
designers in considering and making technical                                 Multi-spatial resolution reduces rendering quality
decisions when designing new methods. We classify                          in the output image according to the visual acuity
the current foveated rendering methods according                           models and the spatial CSFs from the foveal to the
to three dimensions: (1) required input data type;                         peripheral region. Multi-temporal resolution based


Table 1   The classification matrix is produced by combining RDF classification (letters) with motion classification (numbers) from Spjut et al. [98]

                               Class A                         Class B                          Class C                          Class D
                          Acuity Matched                  Foveally Matched               Peripherally Matched             Non-Acuity Matched
                    For any gaze direction, the                                         The foveal inset fails to      Neither the foveal inset nor
                                                      For any gaze direction the                                         periphery matches user
                     display meets or exceeds                                           match user acuity, but
  Class 1 Fully                                        foveal inset matches user                                         acuity, but the display
                      the user’s visual acuity                                         achieves equal resolution
    Foveated                                             acuity, but peripheral                                         achieves equal resolution
                      without any peripheral                                            over all gaze directions
                                                          artifacts are present                                          over all gaze directions
                             artifacts                                                with no peripheral artifacts

                                                                                         The foveal inset fails to     Neither the foveal inset nor
                     For a practical sub-set of       For a practical sub-set of                                         periphery matches user
                                                                                         match user acuity, but
     Class 2        gaze directions the display       gaze directions the foveal                                         acuity, but the display
                                                                                        achieves equal resolution
   Practically      meets or exceeds the user’s       inset matches user acuity                                         achieves equal resolution
                                                                                       over a practical sub-set of
    Foveated        visual acuity without any           w peripheral artifacts                                         over a practical sub-set of
                                                                                         gaze directions with no
                        peripheral artifacts                   present                                                       gaze directions
                                                                                           peripheral artifacts

                                                                                        The foveal inset fails to      Neither the foveal inset nor
                    For a small sub-set of gaze                                                                          periphery matches user
                                                     For a small sub-set of gaze        match user acuity, but
     Class 3          directions the display                                                                             acuity, but the display
                                                      directions the foveal inset      achieves equal resolution
    Partially       meets or exceeds the user’s                                                                         achieves equal resolution
                                                        matches user acuity w         over a small sub-set of gaze
    Foveated        visual acuity without any                                                                          over a small subset of gaze
                                                     peripheral artifacts present         directions with no
                        peripheral artifacts                                                                                    directions
                                                                                      peripheral artifacts present
                     For a single gaze direction                                        The foveal inset fails to      Neither the foveal inset nor
                                                      For a single gaze direction
                        the display meets or                                            match user acuity and           periphery matches user
    Class 4                                            the foveal inset matches
                      exceeds the user’s visual                                       foveal acuity changes with          acuity, and the RDF
  Non-Foveated                                         user acuity w peripheral
                         acuity without any                                             gaze, but no peripheral        appears to change for any
                                                           artifacts present
                         peripheral artifacts                                          artifacts are ever present         given gaze direction

204                                                                                                             L. Wang, X. Shi, Y. Liu


                     Table 2       Taxonomy vocabulary                     reduce the resolution of peripheral regions with low
                            a                   Image/Video                luminance-contrast sensitivity more aggressively to
                            b                   Volume Data                further improve foveated rendering performance [29].
                            c                 Geometric Meshes             Foveated rendering alongside the concept of multi-
      1. Data Type
                            d                    Point Cloud               color resolution [99] takes advantage of peripheral
                            e                  Hologram Data               chromatic degradation, i.e., acceptable peripheral
                            f                    Light Field               chromatic LoD, and renders one image with multiple
                            a              Multi-spatial Resolution        color resolutions based on spatio-chromatic CSFs.
                            b             Multi-temporal Resolution
                                                                           Multi-luminance resolution and multi-color resolution
      2. Foveation          c            Multi-luminance Resolution
                                                                           based methods are also spatially multi-resolution;
        Principle           d               Multi-color Resolution
                                                                           however, a particular difference remains in the
                            e                   Level of Detail
                                                                           foveation principle used. To assist readers in more
                            a                   Rasterization
                            b                    Ray Tracing
                                                                           clearly understanding these methods, in this survey,
                            c                    Ray Casting
                                                                           we separated multi-luminance and multi-color
      3. Rendering                                                         resolution based methods from the traditional
                            d                 Instant Radiosity
       Paradigm
                            e                 Shadow Mapping               multi-spatial resolution based methods. LoD reduces
                            f            Online/Offline Simplification     the complexity of the scene geometry in the periphery
                            g                 Neural Rendering             through visual acuity models and CSFs to reduce
                            h                  Photon Mapping              computing resources required to render the virtual
                               i               Phase Retrieval             environment.
                            j                 Data Transmission              The third classification dimension is the rendering
                                                                           paradigm used by existing methods to achieve multi-
methods render one image with multiple resolutions                         resolution rendering, which includes: rasterization, ray
based on spatio-temporal CSFs. Researchers not                             tracing, ray casting, instant radiosity, shadow mapping,
only consider the HVS spatial error tolerance                              online/offline simplification, photon mapping, neural
but also the spatio-temporal error tolerance of                            rendering, and phase retrieval for holographic data.
dynamic objects and take advantage of the HVS                              For the 360◦ video which is extremely popular in VR
to ensure greater spatio-temporal error tolerance                          applications recently, the encoding, decoding, and
of dynamic objects to effectively perform foveated                         transmission mode combined with foveal information
rendering, which achieves significant improvement                          directly affect foveated rendering, Thus, we also
in speed [81, 88]. Multi-luminance resolution based                        introduce the data transmission of the 360◦ video
methods render one image with multiple resolutions                         as an element of the rendering paradigm.
according to spatio-luminance CSFs. Based on the                             Table 3 shows the classification of 90 published
HVS luminance-contrast-awareness, researchers                              reports on the foveated rendering methods from


            Table 3     Summary of foveated rendering technique implementations (*: survey, +: patent, -: cutting-edge equipment)

                    Implementation                             Data Type         Foveation Principle             Rendering Paradigm
                Levoy 1990 I3D [35]                               b                      a                                c
        Funkhouser 1993 SIGGRAPH [100]                               c                   e                                f
              Ohshima 2002 VR [58]                                   c                   e                                f
            Luebke 2000 Tech.Rep [59]                                c                 a, b, e                            f
               Luebke 2001 EG [19]                                   c                  a, e                              f
            Parkhurst 2001 ETRA [60]                                 c                   e                                f
              Loschky 2001 ARL [18]                                a                     a                                a
              Reddy 2001 CGA [101]                                   c                  b, e                              f
                Yee 2001 TOG [81]                                    c                   b                                a
              Murphy 2001 EG [102]                                   c                   e                                f
                                     ∗
             Parkhurst 2002 HF [23]                                /                     /                                /
              Cheng 2003 SPA [103]                                   c                   e                                f

Foveated rendering: A state-of-the-art survey                                                           205


                                                                                                  (Continued)

               Implementation                   Data Type   Foveation Principle   Rendering Paradigm
        Duchowski 2004 Citeseer∗ [104]              /               /                     /
                              ∗
         Reingold 2003 SAGE [105]                   /               /                     /
            Zhou 2004 BDM [106]                    b                a                     c
              Yu 2005 VC [107]                     b                a                     c
              Lu 2006 EG [108]                     b                a                     c
        Duchowski 2007 TOMM∗ [96]                   /               /                     /
          Hillaire 2008 CG&A [109]                  c               a                     a
            Hillaire 2008 VR [66]                   c               a                     a
          Duchowski 2009 TAP [99]                   a               d                     a
           Murphy 2009 SAP [110]                    c               a                     c
          Mantiuk 2011 SGDA [67]                    c               a                     a
           Guenter 2012 TOG [26]                    c               a                     a
            Gallo 2013 ISRN [111]                  b                a                     c
          Duchowski 2014 SAP [24]                   c               a                     a
      Fujita 2014 SIGGRAPHAsia [112]                c               a                     b
     Vaidyanathan 2014 Eurographics [61]            c               a                     a
           Mauderer 2014 CHI [69]                   c               a                     a
       Patney 2016 SIGGRAPH− [113]                  /               /                     /
            Patney 2016 TOG [88]                    c               b                     a
            Stengel 2016 CGF [28]                   c              b, c                   a
           Swafford 2016 SAP [114]                  c              a, e                  a, f
         Pai 2016 SIGGRAPH− [115]                   /               /                     /
             Lindeberg 2016 [116]                   c               e                      f
           Koskela 2016 ISVC [31]                   c               a                     b
            Weier 2016 CGF [62]                     c               a                     b
             Weier 2017 EG [39]                     /               /                     /
            Albert 2017 TAP [117]                   a               a                     a
       Blackmon 2017 USPatent+ [118]                c              a, e                 a, b, f
        Koskela 2017 SIGGRAPH [119]                 c               a                     b
             Hsu 2017 MM [120]                      a               a                     a
             Sun 2017 TOG [121]                     f               a                     b
          Lungaro 2018 TVCG [122]                   a               a                      j
            Meng 2018 TOG [123]                     c               a                     a
           Koskela 2018 CVM [124]                   c               a                     b
             Turner 2018 VR [25]                    c               a                     a
             Molenaar 2018 [32]                     c               a                     b
             Weier 2018 TAP [71]                    c               a                     b
            Zheng 2018 VRST [20]                    c                e                     f
        Tan 2018 Opt.Express− [125]                 /               /                     /
        Wilson 2018 USPatent+ [126]                 a               a                     a
         Young 2019 USPatent+ [127]                d                a                     a
          Kaplanyan 2019 TOG [38]                   a               a                     g
          Wei 2019 Appl.Opt. [128]                  e               a                     b
         Young 2019 USPatent+ [129]                 c               e                      f
        Tavakoli 2019 USPatent+ [30]                /               /                     /
        Stafford 2019 USPatent+ [130]               c                e                     f
            Tursun 2019 TOG [29]                    c               c                     b
            Koskela 2019 EG [33]                    c               a                     b
           Friston 2019 TOG [131]                   c               a                     a
             Schütz 2019 VR [21]                  d                e                      f

206                                                                                       L. Wang, X. Shi, Y. Liu


                                                                                                        (Continued)

              Implementation               Data Type           Foveation Principle        Rendering Paradigm
         Bruder 2019 EuroVis [37]              b                       a                          c
        Radkowski 2019 HCII [132]              c                       a                          a
         Siekawa 2018 MMM [133]                c                       a                          b
          Kim 2019 TOG− [134]                  /                       /                          /
        Lee 2019 Opt.Express− [135]            /                       /                          /
        Bastani 2020 USPatent+ [27]            c                       a                          a
          Spjut 2020 TVCG∗ [98]                /                       /                          /
        Young 2020 USPatent+ [136]             c                       a                         a, e
             Koskela 2020 [34]                 c                       a                          b
          Kang 2020 ACCESS [72]                b                       a                          c
        Ananpiriyakul 2020 EI [137]            b                       a                          c
          Wang 2020 ISMAR [36]                 c                        c                         d
          Konrad 2020 TOG [138]                c                       a                          a
          Joshi 2020 Access [139]              c                       a                          a
           Meng 2020 TVCG [75]                 c                       a                          a
          Meng 2021 TVCG [140]                 f                       a                          a
          Frieß 2021 TVCG− [141]               /                       /                          /
                          −
           Yoo 2020 OpEx [142]                 /                       /                          /
       Bitterli 2020 SIGGRAPH [143]            c                       b                          c
              Deza 2020 [144]                  a                       a                          g
           Yang 2021 C&G [145]                 c                        c                         d
          Franke 2021 CGF [146]                c                      a, b                        a
             Surace 2021 [147]                 a                       a                          g
          Kim 2021 ISMAR [148]                 c                       a                          b
           Liu 2021 ISMAR [149]                c                       a                          b
          Walton 2021 TOG [150]                a                       a                          a
            Li 2021 TVCG [151]                 a                       a                          j
           Shi 2021 TVCG [152]                 c                       c                          h
      Chakravarthula 2021 TVCG [153]           e                       a                          i
          Jindal 2021 TOG [154]                c                      b, c                        a



1990 to 2021 according to the three dimensions. In       complexity of geometric meshes, simulating visual
addition, the table also lists publications on new       blur effects to enhance the visual appearance of the
devices for foveated rendering (marked with “-”), the    rendering results by rasterization on geometric meshes
related surveys (*), and the related patent (+).         and accelerating the ray casting process for rendering
                                                         volume data. With the emergence of Ray Tracing
                                                         Texel eXtreme (RTX), a high-end professional visual
4     Early research from 1990 to 2011
                                                         computing platform created by Nvidia that supports
As foveated rendering research is plentiful spanning     real-time ray tracing [155], recent research in foveated
a period greater than 30 years, it is divided into two   rendering paid more attention to accelerating ray
parts organized by chronological order: early research   tracing for geometric meshes. Prior to the emergence
from 1990 to 2011 and recent research over the last      of RTX, previous ray tracing was only available for
10 years from 2012 to 2021.                              non-real-time applications, such as offline rendering
  One reason for this is that, with the development      for cinematic visual effects or photo-level realism
of technology, the focus of the recent research has      [156].
changed compared with early research.                      Secondly, recent developments in other technologies
  Firstly, the early research in this topic area         have also led to a change in foveated rendering
focused on developing LoD techniques to reduce the       focus. For example, cloud rendering became a trend

Foveated rendering: A state-of-the-art survey                                                                            207


with the development of communication technologies
such as 5G, which enables content providers to
render 3D programs using a remote server and send
back rendered images to user terminals interactively
[157]. Cloud rendering has revolutionized foveated
rendering-based data transmission. The development
of deep learning techniques has also used foveated       Fig. 6 Frequency of research in foveated rendering from 1990 to
                                                         2011. Numbers in parentheses indicate the number of studies using
images or videos to improve the accuracy of deep         the specific data type, and foveated principle and rendering paradigm
learning models for specific computer vision tasks.      are listed in front of parentheses.
These key developments have initiated vital research
hotspots in the field.
   Thirdly, researchers proposed new data types, such    spatial resolution for volume data (Section 4.3); (3)
as point cloud, hologram data, and light fields,         foveated rendering based on multi-spatial resolution
to meet the requirements of different applications.      for geometric meshes (Section 4.4). Additionally,
Incorporating the rendering paradigm for these new       some techniques closely related to foveated rendering
data types into the foveated rendering framework has     in early research are introduced (Section 4.5). In
also become a critical research area.                    early research, foveated rendering was also referred
   Another reason for this division is that readers      to as gaze-directed rendering (GDR), gaze-contingent
may have different requirements for early and recent     rendering (GCR), or gaze-contingent display (GCD).
research. For the former, typically readers solely
require understanding of the methods function and        4.1    Reviews
fundamental ideas. While for the latter, because it is   Several reviews discuss and summarize the early
the state of the art, it may be necessary to reproduce   foveated rendering research.
and compare recent research, such that readers can         For example, Reingold et al. [105] discussed gaze-
establish a deeper understanding of contemporary         contingent multi-resolution displays (GCMRD) in
foveated rendering.                                      different areas, including engineering design research
   Foveated 3D graphics [26] proposed in 2012 is an      on the development of GCMRDs, multi-resolution
essential milestone for dividing research on the topic   image processing, multi-resolution sensors, human
into two parts. This introduced a rasterization-based    factors research on multi-resolution displays, gaze-
foveated rendering system to improve rasterization       contingent displays, and human–computer interaction.
rendering performance, demonstrating that users          Focus was placed on reviewing methods to solve two
cannot perceive the degradation of rendering quality     questions regarding gaze-contingent multi-resolution
from foveated rendering in this system because of        displays: (1) image degradation owing to the charac-
the publication of extremely detailed perceptual         teristics of multi-resolution images, vision model
experiments. Prior to this, foveated rendering           based multi-resolution images generation methods,
primarily mimicked HVS visual effects to improve the     discrete/continuous-resolution drop-off, and color
visual appearance of images. In subsequent research,     resolution drop-off were reviewed; (2) for perceptible
foveated rendering focused on improving rendering        image motion caused by image updating, gaze/
performance without perceptual loss.                     head/hand-contingent displayed area of interest (D-
   In this section, early foveated rendering research    AOI) movement-based methods and predictive D-AOI
is reviewed. Figure 6 visualizes the frequency of        movement-based methods were analyzed. Parkhurst
various research on the topic from 1990 to 2011          and Niebur [23] reviewed variable-resolution displays
according to the proposed taxonomy. We initially         from the three aspects: (1) potential computational
summarized discussions in review papers from 1990 to     savings achieved with variable-resolution displays;
2011 (Section 4.1). Subsequently, we introduced the      (2) practical constraints in implementing variable-
methods according to their frequency of occurrence       resolution displays; (3) the behavioral consequences
from high to low: (1) foveated rendering based on LoD    of using variable-resolution displays, such as per-
(Section 4.2); (2) foveated rendering based on multi-    ceptual quality, task performance, and eye movement

208                                                                                           L. Wang, X. Shi, Y. Liu


measures. The authors also explained that gaze-              for gaze direction. The authors introduced a visual
related rendering in virtual reality is only one variable-   acuity fall-off model, a binocular horopter model, and
resolution display application. Variable-resolution          a kinetic vision model, respectively, to calculate visual
displays could also be used in low-vision enhancement        acuity according to eye direction, and subsequently
and internet image transmission applications.                mapped the minimum visual acuity calculated by the
Duchowski et al. [104] divided gaze-contingent display       three models to control the LoD for rendering.
methods into two categories: model-based graphical              As the discrete LoD technique cannot locally
displays and screen-based displays. Model-based              change details, for example, the side of a large object
methods used the objects’ LoD to generate the                near the view cannot be rendered in great detail
image matching the resolvability of the human retina,        while simultaneously reducing its distant details.
while the screen-based methods adjusted the image            Rather than calculating a series of static LoDs in
quality at the pixel level. Focus plus context               the pre-process, Hoppe [160] introduced the concept
methods were also discussed, which were extremely            of continuous LoD. They built a data structure from
similar to foveal and peripheral displays. Duchowski         which the desired LoD can be extracted at runtime.
and Çöltekin [96] reviewed perceptually loss-less          In foveated rendering, Luebke et al. [59] proposed
gaze-contingent displays, space-variant imaging              a gaze-directed continuous LoD framework. They
based on the pyramidal idea, and gaze-contingent             employed a commercial eye tracker to measure the
displays for stereoscopic imaging. The authors also          user’s gaze over a desktop display in real time, and
summarized GPU-based gaze-contingent displays                then introduced a perceptual metric to measure the
before 2007 and introduced related technologies              level of geometric meshes based on the visual acuity
including mipmapping, multitexturing, and fragment           fall-off model proposed in Ref. [161] and the spatio-
programming.                                                 temporal contrast sensitivity function proposed in
                                                             Ref. [49]. Murphy and Duchowski [102] employed
4.2   LoD                                                    a binocular eye-tracked VR system to obtain the gaze
Clark [158] introduced the concept of discrete LoD,          in VR, and then modeled visual acuity fall-off for
which defined several versions of the model at               both eyes based on the gaze. Subsequently, they
different levels, using a detailed grid when the object      proposed the gaze-contingent continuous LoD to
is close to the observer and replacing it with a             degrade the resolution of meshes based on visual
coarser approximation when the object is far from            acuity. Luebke and Hallen [19] provided a perception
the observer. The LoD technique can be combined              based node fold system for the vertex tree, which is
with foveated rendering to reduce the complexity             a hierarchical clustering of vertices. They identified
of scenes according to the user’s gaze position and          that the perceptible result of a change induced by
the perceptual models, which significantly improves          simplification can be conservatively equal to the
time performance [159]. Funkhouser and Séquin [100]         change of its lowest spatial frequency and maximum
proposed a gaze-directed dynamic LoD selection               contrast. Thus the perception-based node expansion
system that considers motion blur and visual acuity.         system visits each node in the vertex tree top–down.
The motion blur value is expressed by the speed at           If the lowest spatial frequency and maximum contrast
which the object image moves on the retina. The              induced by folding the node are less than the pre-
visual acuity value is expressed by the distance from        defined threshold contrast, the system folds the
the object to the center of the user’s gaze. Owing to        node. Otherwise, the node will remain unfolded,
the lack of an accurate perceptual model, the effect         and traversal continues. Reddy [101] noted that
of motion blur is controlled by a slider set by the          previous perceptually based LoD research used pre-
user. As there is no eye-tracking system, the user’s         simplified versions of an object that can be selected
gaze is assumed to be at the center of the screen.           for rendering in a view-dependent manner. They
This research firstly introduced the concept of gaze-        performed a per-pixel calculation of the pixel’s spatial
directed perceptual LoD. Ohshima et al. [58] used            frequency by employing the GPU, and then used
the ultrasonic sensors built into the eye-trackers to        the spatial frequency to determine the LoD based
measure head direction, which is used as a substitute        on an eccentricity-based spatio-temporal CSF [49].

Foveated rendering: A state-of-the-art survey                                                                              209


Parkhurst et al. [60] conducted virtual search tasks to
evaluate straight-forward gaze-contingent continuous
LoD rendering, in which the LoD decreases linearly
as the distance from the rendered object to the
point of gaze increases. The results demonstrated
that the behavioral performance gains could offset
behavioral performance costs of gaze-contingent LoD
techniques owing to increased rendering performance.
                                                           Fig. 7      Fast rendering of foveated volumes in wavelet-based
Cheng [103] used surface information obtained from         representation proposed by Yu et al. [107]. (a) is rendered with
a 3D scanner and allowed a user to select a foveal         a full resolution, (b) is rendered with this method, and the fovea is
point, and then proposed an interactive LoD update         situated at the red dot. This method achieved a 1.3–8× improvement
                                                           in speed compared with the full resolution ray casting. Reproduced
with foveation.                                            with permission from Ref. [107], c Springer-Verlag 2005.

4.3   Multi-spatial resolution for volume data
Rendering volume data inherently consumes massive          CSF [49] to acquit the HVS importance information,
computing resources owing to large data size. Thus         subsequently, they used this importance information
real-time rendering of large volume datasets was           to fix object shapes, positions and to tune opacity
infeasible using desktop personal computers in earlier     transfer functions automatically.
years. One solution is to use ray casting to render
volume data based on the concept of multi-spatial          4.4     Multi-spatial resolution for geometric
resolution, i.e., to render objects in the foveal region           meshes
at full resolution and ignore details of objects in the    In addition to volume data, the concept of multiple
peripheral region, which can reduce calculation and        spatial resolution is also used to accelerate geometric
communication requirements.                                mesh rendering.
   Levoy and Whitaker [35] first explored the method          Murphy et al. [110] proposed a hybrid technique
for incorporating foveated rendering into volume           based on the visual acuity fall-off model and the
rendering. They used the Eye-Mark eye tracker to           spatial CSF, which used ray casting to sample
obtain the user’s gaze direction and directed this at      the scene’s geometry. This technique enables non-
an object by rotating the user’s eyes or head until the    isotropic degradation within meshes without directly
object’s projection falls on the fovea. Subsequently,      manipulating mesh geometry.
they distributed the number of casting rays per unit          As early geometry models were coarse, geometric
area and the number of samples taken along the unit        mesh performance rendering in the entire image at
length of each ray based on a visual acuity fall-off       high resolution is acceptable. Thus, researchers in
model. For weakening unnecessary objects in the            foveated rendering focused more on simulating the
peripheral region, Zhou et al. [106] adjusted the          HVS visual appearance, i.e., gaze-contingent depth-
opacity of the sample according to the distance from       of-field (DoF) rendering, rather than accelerating
the sample point to the center of the foveal region        geometric mesh rendering. The traditional pinhole
for volume feature enhancement, which assisted users       camera model in computer graphics can sharply
in focusing more on objects in the foveal region. To       present objects at all distances. However, in the
further accelerate foveated volume rendering, Yu et        eyes and real cameras, only objects within the focal
al. [107] remapped the mask which was used to              range can be sharply displayed, while objects far away
sample the rays and the length of each ray into a          or close to the viewpoint are blurred. To simulate
small number of wavelet coefficients in the wavelet        the fact that humans only perceive sharp objects
domain according to the visual acuity fall-off model.      within a certain distance range near the focal length
Figure 7 visualizes the rendering results of full-         and to improve the user’s immersion, gaze-contingent
resolution ray casting and the proposed method. Lu         DoF rendering was introduced in Hillaire et al. [66]
et al. [108] used a camera to focus on one eye and         and Mantiuk et al. [67]. In this review, we regard
record eye movements as the user observes the volume,      gaze-contingent DoF as a specific type of foveated
and employed the eccentricity-based spatio-temporal        rendering, which pays more attention to the scene

210                                                                                        L. Wang, X. Shi, Y. Liu


depth range in the foveal region.                         in foveated rendering are highly related to the HVS
  For improving gaze-contingent DoF perception            foveal features.
during first-person navigation in virtual environments       In early research involving perception-based
(VE), Hillaire et al. [109] proposed a gaze-contingent    rendering, researchers conducted user studies of
DoF blur filter which simulates the blurring of objects   perceptual models to obtain useful parameters
located in front of or behind the focus point of the      and error metrics that have a direct impact on
eyes, and a peripheral blur filter which simulates        foveated rendering. For example, Ramasubramanian
the blurring of objects situated in the periphery of      et al. [162] introduced an error metric considering
the field of vision. Hillaire et al. [66] subsequently    the spatial-luminance CSF, which predicted the
described an algorithm for calculating the focal length   perceptual threshold to detect artifacts in 3D scenes.
and point in the 3D virtual environment and used the      Myszkowski et al. [163] presented a perceptual
gaze-contingent DoF blur and peripheral blur filters      error metric based on a spatio-temporal CSF, which
proposed in Hillaire et al. [109] to render the DoF       retained inherent noise in the animation generated
blur effects to simulate the fact that humans only        using stochastic methods below human observer
perceive sharp objects within a certain distance range    sensitivity.
near the focal length. Mantiuk et al. [67] evaluated         Focus+context visualization is a rendering
human impression regarding the existence of the           technique that visualizes more critical information
DoF phenomenon in the 3D virtual environment.             by removing or suppressing less critical parts of the
The results demonstrated that people noticed and          scene. Critical information typically has semantic
preferred the DoF visualization controlled by the eye     integrity. Focus+context visualization typically uses
tracker. The best impression was achieved with the        distortion and highlighting to visualize interested
medium blurriness level (the lens aperture diameter       objects in focus and nearby related objects in context
was 7 cm).                                                [164–171], while foveated rendering is based on HVS
  In early foveated rendering research, researchers       perception theories to allocate further computing
also adopted concepts of multi-color and multi-           sources to the foveal region.
temporal resolution in foveated rendering. Duchowski         Carpendale et al. [167] highlighted data by
et al. [99] investigated the color reduction in the       dedicating additional space to this and applied
peripheral region. The results demonstrated that          distortions to abstract graphs to observe interested
peripheral chromaticity could not be reduced within       graph nodes clearly. Viola et al. [171] proposed a
the central 20◦ visual angle, i.e., the color reduction   view-dependent model for automatic focus+context
should be maintained isotropically across the central     volume visualization. This model enables interested
20◦ visual field.                                         objects to be displayed more accurately to view
                                                          further details, while occluded objects are displayed
4.5   Other related work                                  with low accuracy or completely suppressed.
From 1990 to 2011, some other related foveated               Selective rendering is task-dependent rendering,
rendering research emerged, such as perception            which uses HVS knowledge to select the objects in
based rendering, focus+context visualization, selective   scenes that require rendering based on application
rendering, and multi-resolution display.                  tasks [172–175], i.e., different tasks require different
  Perception-based rendering refers to use of the         objects to be drawn. For example, if the task is to
HVS features and associated perceptual models to          count the number of pencils in a mug on a table in
improve rendering performance and to enhance the          a room, only the image in the visual angle of the
perceptual quality of rendering results. For example,     fovea centered around the pencils is rendered with
Yee et al. [81] constructed a spatio-temporal error       high quality. Cater et al. [172] designed perceptual
tolerance map based on a spatio-temporal CSF that         experiments to prove that users would ignore parts
accepts low-quality rendering in highly error-tolerant    of the scene that were not related to a specific task,
regions without degrading perceptual quality, thus        which can be used to reduce rendering time without
improving rendering speed. Unlike perception-based        affecting visual quality in interactive tasks. Sundstedt
rendering, all HVS features and perceptual models         et al. [174, 175] investigated the extent to which

Foveated rendering: A state-of-the-art survey                                                                            211


image resolution, edge anti-aliasing and reflection,
and shadow parameters can be reduced between non-
task-related and task-related regions when viewers
cannot perceive image quality degradation.
   Multi-resolution display focused on a more general
pipeline of multi-resolution rendering [51, 176–179].
In addition to foveated rendering, the multi-
resolution display can also be used for perception-
based and selective rendering, etc. Duchowski
and McCormick [176] introduced a multi-resolution
display method based on mipmap texture mapping.
They retained the original image resolution in           Fig. 8 Frequency of research in foveated rendering from 2012 to
multiple regions of interest (ROIs) selected by users    2021. Numbers in parentheses indicate the number of studies using
                                                         the specific data type, and foveated principle and rendering paradigm
and gradually reduced the periphery around each          are listed in front of parentheses.
ROI according to the specified resolution mapping
function. Geisler and Perry [51] developed a foveated
                                                         spatial resolution rasterization methods for geometric
multi-resolution pyramid video coding/decoding
                                                         meshes, and multi-spatial resolution methods for
system that uses a foveated multi-resolution pyramid
                                                         volume data remain research hotspots. Furthermore,
to encode each image into five or six regions of
                                                         methods such as multi-spatial resolution ray tracing
different resolutions and eliminated spatial edge
                                                         for geometric meshes, and multi-spatial resolution
artifacts between the regions generated by foveation
                                                         methods for images or videos have also attracted
through raised-cosine blending across levels of the
                                                         keen attention from researchers. In the following
pyramid and “foveation point interpolation” within
                                                         subsections, we introduce methods in these classes
pyramid levels. Geisler and Perry [177] described a
                                                         according to the frequency of occurrence from high
multi-resolution pyramid method that used a pyramid
                                                         to low: (1) foveated rendering based on multi-
encoder to divide the image into 2–6 layers, and
                                                         spatial resolution, rendering geometric meshes with
used a pyramid decoder to sample each layer at
                                                         rasterization (Section 5.1); (2) foveated rendering
different rates. Parkhurst et al. [178] introduced
                                                         based on multi-spatial resolution, rendering geometric
a two-region gaze-contingent display and investigated
                                                         meshes with ray tracing (Section 5.2); (3) foveated
behavioral effects on the display based on a visual
                                                         rendering based on multi-spatial resolution, rendering
search task. They identified that reaction time and
                                                         image/video data (Section 5.3); (4) foveated
accuracy co-vary as a function of the foveal region
                                                         rendering based on LoD (Section 5.4); (5) multi-
size. For the small foveal region, slow reaction time
                                                         spatial resolution for volume data (Section 5.5);
is accompanied by high accuracy. Conversely, for the
                                                         (6) multi-luminance resolution method for geometric
large foveal region, fast reaction time is accompanied
                                                         meshes (Section 5.6); and (7) foveated rendering for
by low accuracy. Geisler and Perry [179] proposed
                                                         nascent data types (Section 5.7).
a method to generate completely arbitrary variable-
resolution displays based on image pyramidal pre-        5.1    Multi-spatial resolution rasterization for
processing [51].                                                geometric meshes
                                                         In recent years, with the development of modeling
5   Foveated rendering over the past                     technology, the complexity of 3D models and the
    decade (2012–2021)                                   scale of virtual scenes have increased. In multiple
                                                         virtual reality applications, using high-resolution and
This section reviews foveated rendering research         high-quality rasterization of the scene cannot achieve
published most recently over the past decade.            real-time frame rates. Therefore, many researchers
Figure 8 visualizes the frequency of various foveated    focused on the foveated rendering method alongside
rendering research from 2012 to 2021 according to        improving geometric mesh rasterization performance
the proposed classification method. LoD or multi-        based on the concept of multi-spatial resolution.

212                                                                                                                  L. Wang, X. Shi, Y. Liu


  Guenter et al. [26] took advantage of the visual                          Pixel Shading (CPS) and tested the architecture for
acuity fall-off model and rendered three nested layers                      foveated rendering with a visual acuity fall-off model.
by rasterization. The pipeline for this method is                           As CPS pipelines require adaptive shading features
described in Fig. 9. These nested layers are rasterized                     not yet commonly available on commodity GPUs,
as the angular diameter decreases in resolution to                          Meng et al. [123] presented a simple two-pass kernel
achieve improved rendering performance. Finally,                            foveated rendering (KFR) pipeline that maps well
three layers are mixed to form the final image. The                         onto modern GPUs. In the first pass, they computed
results demonstrate that the rendering speed of this                        the kernel log-polar transformation and rendered
method is 5–6× that of the traditional method.                              it to a reduced-resolution buffer. The second pass
The quality users visually perceive is comparable                           carried out the inverse-log-polar transformation with
to traditional rendering. Vaidyanathan et al. [61]                          anti-aliasing to map reduced-resolution rendering to
presented a novel architecture to flexibly control                          the full-resolution screen. The results showed that
shading rates in a rasterization pipeline named Coarse                      KFR could achieve a 2.8–3.2× speed improvement
                                                                            in rendering on 4K UHD (2160 p) displays with less
                                                                            perceptual LoD.
                                                                               In addition to considering the spatial factor, much
                                                                            research considered the temporal factor, based on
                                                                            the concept of multi-temporal resolution to further
                                                                            accelerate geometric mesh rasterization. Stengel et
                                                                            al. [28] introduced a sampling method based on
                                                                            the visual acuity fall-off model, the spatio-temporal
Fig. 9 Foveated 3D graphics proposed by Guenter et al. [26]. Three          and the spatio-luminance CSFs, and subsequently
nested layers were rendered (red, green, and blue) at three different       integrated the sampling method into the deferred
resolutions through rasterization based on a visual acuity fall-off
                                                                            shading pipeline. Only important image features were
model. The three nested layers are combined to generate the final
image. This method could achieve comparable perceptual quality with         shaded while interpolating the remaining features
reference to traditional full-resolution rendering, but at a 4–6.2× speed   without affecting perceived quality. The visualization
improvement. Reproduced with permission from Ref. [26], c ACM
2012.                                                                       results are shown in Fig. 10. Patney et al. [88]




Fig. 10 Adaptive image-space sampling method for foveated rendering proposed by Stengel et al. [28]. A perceptual adaptive sampling pattern
(b) was constructed for sparse shading (c), which combined visual cues such as visual acuity (a), spatial, spatio-temporal, and spatio-luminance
CSFs. Fast image interpolation was performed in the periphery (d) to achieve the same perceptual quality with less shading cost. Row 2 shows
the pipeline of the proposed method: in the geometry pass, this generates the G-Buffer; in the deferred pass, it first generates the sampling
pattern, then performs sparse shading based on the sampling pattern, and finally uses a pull-push operation to complete the missing image
parts by interpolation; in the post-processing pass, it applies post-processing operations similarly to tone mapping and grading before displaying
the final image. The final image contains high details in the fovea and low details in the periphery. Reproduced with permission from Ref. [28],
 c The Eurographics Association and John Wiley & Sons Ltd. 2016.

Foveated rendering: A state-of-the-art survey                                                                213


designed a foveated rendering system that reduces         multiple parameters, such as the number of layers,
the number of shadings by up to 70%, and the              eccentricity, resolution of the peripheral region, and
authors subsequently introduced a novel anti-aliasing     foveated rendering perceptibility must be evaluated.
algorithm based on a visual acuity fall-off model and     Therefore, many researchers designed perceptual
a spatio-temporal CSF. This anti-aliasing algorithm       studies to optimize and evaluate the task. Patney
assists in recovering peripheral region details that      et al. [88] designed a user study to evaluate
are resolvable by human eyes albeit degraded by           users’ perceptual abilities of peripheral vision when
filtering. Franke et al. [146] presented a foveated       viewing today’s displays. The results demonstrated:
rendering method that comprised recycling pixels          (1) filtering peripheral regions would reduce contrast,
in the periphery by spatio-temporally reprojecting        thereby creating a sense of tunnel vision; (2) when
them from previous frames to accelerate rendering         applying the post-processing contrast enhancement
performance. This reprojection detected and re-           function, the object could tolerate a 2× larger blur
evaluated artifacts and disocclusions according to        radius before detecting the difference from the non-
a confidence value determined by a perception-based       foveated ground truth. Swafford et al. [114] applied
metric. Jindal et al. [154] proposed the variable-rate    foveated rendering to the multi-resolution, screen-
shading pipeline to accelerate rasterization rendering    space ambient occlusion, and tessellation methods.
performance. This approach divides the output image       Practical rules for each method were proposed to
into a number of 16×16 image tiles, and subsequently      achieve significant performance gains with user studies
adaptively adjusts the shading accuracy and refresh       and the newly proposed rendering quality metrics.
rate of each image tile based on spatio-temporal and         Recent research also concentrated on gaze-
the spatio-luminance CSFs.                                contingent DoF rendering based on the concept
   To further improve calculation process speed,          of multi-spatial resolution. Mauderer et al. [69]
Turner et al. [25] aligned the rendered pixel grid        designed a user study to demonstrate that gaze-
to virtual scene content during rasterization and         contingent DoF increased subjective perceived realism
upsampling, which reduced the detectability of            and depth and could contribute to the perception
motion artifacts in the periphery without complex         of ordinal depth and distance between objects;
interpolation or anti-aliasing algorithms. Bastani        however, it was limited in accuracy. Duchowski
et al. [27] rendered an intermediary image of the         et al. [24] used gaze-contingent DoF to reduce
3D scene in the intermediary compressed space             users’ visual discomfort when viewing stereoscopic
and unwarped the image to generate the foveated           displays. However, similar to earlier attempts,
image. Young et al. [136] adopted foveated rendering      participants disliked gaze-contingent DoF, which may
to accelerate shadow rendering. Shadow mapping            be attributed to eye tracker spatial inaccuracy and the
was used to obtain two shadow maps of different           DoF simulation’s noticeable temporal lag. Konrad
resolutions and geometric meshes in the foveal region     et al. [138] extended gaze-contingent DoF rendering
were rendered with the high-resolution shadow map,        to ocular parallax rendering, which described the
while that of the peripheral region were rendered         small amounts of depth-dependent image shifts on
using the low-resolution shadow map.                      the retina created as the eye rotates. They introduced
   Towards HMDs with latency and field-of-                ocular parallax rendering technology that accurately
view requirements, Friston et al. [131] presented         rendered small amounts of gaze-contingent parallax
a rasterization pipeline that achieved foveated           capable of improving depth perception and realism in
rendering in one rasterization pass with per-fragment     VR. The results demonstrated that ocular parallax
ray-casting. Meng et al. [75] accelerated foveated        rendering provided an effective ordinal depth cue
rendering on HMDs with more aggressive foveation          and improved the impression of realistic depth in
based on the theory of ocular dominance.                  VR. Walton et al. [150] believed that the HVS
   Foveated rendering improves the frame rate and         perceives that the periphery is more than just blurry,
quality of foveal vision by reducing peripheral vision    and proposed a real-time method to compute images
resolution. However, foveated rendering optimization      identical to ground truth images in terms of peripheral
is a difficult task. This requires careful selection of   perception.

214                                                                                        L. Wang, X. Shi, Y. Liu


  In addition, researchers applied foveated rendering     the foveal region and rasterization to render the
to VR interaction. Joshi and Poullis [139] presented      peripheral region. To speed up previewing the
foveated rendering-based redirected walking in VR,        artist’s points of interest, Koskela et al. [119, 124]
which capitalized on naturally occurring saccades         applied foveated rendering to progressive Monte
and blinks to completely refresh the framebuffer.         Carlo rendering, which omits more than 90% of
Radkowski and Raul [132] conducted a user study           rays that must be traced in real time. Their user
to demonstrate whether the foveated rendering             study demonstrated that the perceived convergence
technique would distract users and reduce their           of the proposed method was 10× faster than that of
training effect in VE. The results demonstrated that      a conventional preview, and participants rated the
the user noticed the technology but was not negatively    method to have only marginally more artifacts in
affected by it, and the performance difference was        areas where it had to start rendering from scratch.
insignificant, except for some outliers caused by         Molenaar [32] traced rays based on the visual acuity
technical eye-tracking limitations.                       fall-off model, and reconstructed images based on a
  In addition to geometric meshes, multi-spatial          spatial CSF. Experimental results demonstrated that
resolution rasterization can also be used for foveated    this method provided a basic speed improvement of
rendering on point clouds [127].                          4.3×.
                                                            Willberger et al. [180] introduced a hybrid path
5.2   Multi-spatial resolution based ray tracing          tracing approach to accelerate the global illumination
Ray tracing is capable of controlling the number of       calculation in foveated rendering. The method uses
rays emitted from each pixel. The more rays emitted       screen space path tracing to render objects with
from a single pixel, the higher the rendering quality     diffuse, specular, and glossy materials, using multi-
of that pixel. Therefore, the ray tracing framework       bounced path tracing to render objects with the
naturally supports spatial multi-resolution rendering.    transparent material. To render direct lighting
Koskela et al. [31] provided a theoretical estimation     from millions of dynamic light sources interactively
that 94% of the rays could be omitted by integrating      with ray tracing, Bitterli et al. [143] introduced
foveated rendering with ray tracing. Thus many            the spatiotemporal reservoir resampling method to
researchers focused on ray tracing based on foveated      resample a set of candidate light samples based on
rendering with the concept of multi-spatial resolution.   the spatio-temporal feature, and subsequently traced
  Fujita and Harada [112] first implemented the           rays from sampled lights to illuminate the scene. Kim
foveated rendering system based on ray tracing. A         et al. [148] proposed a perceptually efficient pixel
pre-computed sampling pattern was used with a kNN         sampling method suitable for HMD ray tracing, which
scheme to reconstruct images from sparse samples.         combined the Jin et al. [181] selective oversampling
Their system showed artifacts, without considering        technique with the foveated rendering scheme.
the eye sensitivity to contrasts and lacked pertinent       As linear fall-off still requires many rays in the
input from relevant user studies. To address these        periphery [32, 62, 112], Koskela et al. [33] traced rays
challenges, Weier et al. [62] combined ray tracing        and denoised in Visual-Polar space, and subsequently
based foveated rendering with reprojection rendering,     mapped the results to the screen space. In this
using information from the previous frame to reduce       method, when perceived quality is similar, rendering
the sampling rays for new frames. Subsequently, the       and denoising speed will increase by 2.5×, and ray
authors applied a temporal caching and resampling         traversal speed will increase by 1.3–1.5×. This is
scheme to improve reconstruction quality for regions      because primary rays maintain high coherence, and
that expose high contrasts and silhouettes. The           GPU resource utilization is improved. The pipeline
results of user studies conducted demonstrated that       of this method is shown in Fig. 11. Koskela [34]
the method achieved a real-time frame rate and            proposed a working prototype of a foveated ray
compared with the fully rendered image, the visual        tracing system that combined the novel Visual-Polar
difference was difficult to detect. Blackmon et al.       coordinate space proposed in Koskela et al. [33] and
[118] combined ray tracing and rasterization in a         the regression-based reconstruction filter proposed
single pipeline. Ray tracing was used to render           in Koskela et al. [182] for ray tracing that runs in

Foveated rendering: A state-of-the-art survey                                                                                            215




Fig. 11 Foveated real-time path tracing in visual-polar space proposed by Koskela et al. [33]. Rays were traced and rendering results denoised
in a Visual-Polar space, the results were then mapped to the screen space, and finally the Guassian blur was performed to generate the final
HMD rendering result. Ray tracing and denoising in Visual-Polar space increase both by 2.5× faster. Reproduced with permission from
Ref. [33], c The Author(s) 2019.


real time.                                                               to evaluate foveated rendering performance and
  Most previous methods model the sensitivity as a                       quality parameters. Albert et al. [117] explored
function of eccentricity and control the number of                       the effect of foveated rendering latency in VR
rays emitted according to these functions, without                       applications. The results showed that larger foveal
considering that displayed content also strongly                         regions allow for more aggressive foveation, which is
influenced sensitivity. Tursun et al. [29] proposed a                    further pronounced for temporally stable foveation
new luminance-contrast-aware foveated ray tracing                        techniques. The results also demonstrated that
technique. This technique showed that if the spatio-                     increasing eye-tracking latency by 80–150 ms causes
luminance CSF is considered in foveated rendering,                       a significant reduction in the acceptable amount of
the number of tracing rays can be significantly                          foveation; however, a similar decrease in acceptable
reduced. The disadvantage is that a low-quality image                    foveation was not identified for shorter eye-tracking
must be generated for each frame, indicating areas                       latencies of 20–40 ms, suggesting that a total system
with different luminances.                                               latency of 50–70 ms could be tolerated. Hsu et al.
  For applying DoF effects in foveated ray tracing,                      [120] proposed a regression model to demonstrate the
Weier et al. [71] proposed a foveated rendering system                   relationship between human perceived quality and
that integrates DoF filters to hide potential visual                     foveated rendering parameters, such as the number
artifacts. Results of the perceptual study showed                        of layers, the eccentricity degrees, and resolution
that tracing rays reduced by more than 69% while                         of the peripheral region. The results demonstrated
rendering quality of this system was rated almost on                     that (1) no absolute superior subjective assessment
par with full rendering. Liu et al. [149] developed                      method exists, (2) subjects must complete further
a mathematical model to simulate the DoF effects                         observations to confirm that foveated rendering is
of human eyes in VR and subsequently performed                           more imperceptible than perceptible, (3) when the
DoF-based stochastic sampling to simulate retinal                        eccentric angle is 7.5◦ +, and the peripheral region
blur according to this mathematical model.                               resolution is 540 p+, subjects barely notice foveated
                                                                         rendering, and (4) the quality of experiments level is
5.3    Muti-spatial resolution for image/video                           highly dependent on the individuals and scenes.
Muti-spatial resolution for image/video research can                       To further improve foveated rendering speed,
be divided into three categories: (1) conducting                         a small fraction of pixels are provided in the
perceptual research on foveated images or videos;                        peripheral region for each frame, and hence, the
(2) neural rendering on foveated images or videos;                       image quality of the peripheral region is unacceptable.
(3) accelerating the encoding and transmission of                        A neural rendering model was introduced to solve
360◦ video streaming.                                                    this problem. Kaplanyan et al. [38] proposed a
   In the first category, some researchers used high-                    generative adversarial neural network to improve the
quality images/videos taken by cameras or rendered                       quality of images/videos in the peripheral region.
with 3D models to generate foveated images/videos by                     The method can achieve real-time frame rates with
filtering or down-sampling high-quality images/videos                    gaze-contingent head-mounted displays on modern
in the peripheral region and designed user studies                       hardware. Figure 12 compares the results among the

216                                                                                                                L. Wang, X. Shi, Y. Liu




Fig. 12 Neural reconstruction for foveated rendering and video compression proposed by Kaplanyan et al. [38]. The authors reconstructed
the foveated video through a generative adversarial neural network from the sparse foveated video frames with 10% of pixels (top left). This
method reconstructed the video compressed by more than 14× of the original video, and the reconstructed result (top middle) had no significant
reduction in perceptual quality compared with the reference (top right). The recurrent video encoder–decoder network architecture is visualized
in the bottom. Reproduced with permission from Ref. [38], c Owner/Author 2019.



compressed video, reconstructed video, and reference                     located in peripheral regions, streaming 360◦ video
video frames.                                                            based on the fovea is a more efficient solution.
  Some research focuses on improving the accuracy                        Therefore, encoding and transmission of 360◦ video
of deep learning models for specific computer vision                     based on the fovea constitutes important foveated
tasks based on foveated images or videos. Deza                           rendering research. Li et al. [151] proposed a log-
and Konkle [144] explored the visual representation                      linear transformation method to encode original
of the human foveated perceptual system, encoded                         HD 360◦ video frames based on the fovea and
the feature, and trained a convolutional neural                          to transmit them to HMDs, which maintain full-
network named Foveation-Nets to perform scene                            resolution fidelity in the fovea and have improved
categorization. The results demonstrated that the                        perceptual blurring effects in the periphery. Figure 13
visual representation of Fovation-Nets learning was                      compares the final rendering results to the client,
different from the network without foveated input,                       encoded by the traditional log-polar transformation
and Fovation-Nets had an impact on generalization,                       and the log-rectilinear transformation in the server,
robustness, and perceptual sensitivity. This provided                    respectively. To increase the transmission speed
computational support for the idea that the HVS                          of the 360◦ video stream from the server to head-
foveated nature may confer a functional advantage                        mounted displays, Lungaro et al. [122] proposed
for scene representation. Surace et al. [147] proposed                   a gaze-aware transmission approach for 360◦ video
a procedure to train a generative network for foveated                   streaming services, which delivered high visual quality
image reconstruction. This procedure penalized                           images around the users’ gaze points in real time
perceptually significant deviations in the output                        while lowering quality elsewhere. The results of user
to maintain perceived rather than natural image                          studies demonstrated that compared with traditional
statistics.                                                              solutions, the bandwidth required to provide users
  The immersive experience offered in VR via 360◦                        with a high quality of experience level, was reduced
video is becoming increasingly popular. However,                         by up to 83%.
current bandwidth can barely accommodate the
360◦ video streaming solution that delivers the                          5.4     LoD
entire HD 360◦ video frame in real time. As                              In recent years, some research focused on the foveated
most of the pixels in 360◦ video are invisible or                        rendering method based on the LoD technique.

Foveated rendering: A state-of-the-art survey                                                                                            217




Fig. 13 Log-rectilinear transformation for foveated 360◦ video streaming proposed by Li et al. [151]. The upper and lower rows present the
workflows with prior log-polar transformation and the proposed log-rectilinear transformation respectively. Both foveated methods convert the
equirectangular video frames into down-sampled buffers, and subsequently encode and stream buffers to the client. On the client side, buffers
are decoded to the screen space to generate the final results. The log-rectilinear transformation reduces flickering and aliasing artifacts in
both the foveal and peripheral regions more significantly than that of the prior log-polar transformation. Reproduced with permission from
Ref. [151], c IEEE 2021.



Different from previous years, researchers focused                       rendered by approximately 70% and frame time by
on designing user studies to optimize or select various                  approximately 9% compared with using fully adaptive
parameters involved in the previous method or refine                     tessellation.
previous methods instead of proposing new LoD                               Researchers not only applied LoD-based foveated
methods.                                                                 rendering to scenes with geometric meshes, but also
   Swafford et al. [114] designed a user study that                      to point clouds to improve time performance. Schütz
compares a foveated rendered image with an eccentric                     et al. [21] proposed a continuous LoD method for
angle of 9◦ and a reference image at full resolution                     rendering large point clouds in real time. This method
in random order. Three LoDs are generated on                             continuously recreated a down-sampled vertex buffer
the scene geometry: high, medium, and low. A                             from the full point cloud, based on camera orientation,
lower level means that there is a less tessellated                       position, and distance to the camera, in a point-
grid for each tile. The results demonstrated that                        wise fashion and at a speed of 17 million points per
users had a similar visual experience to the foveated                    millisecond.
LoD rendered image with the medium level in the
peripheral region and the full-resolution reference                      5.5     Multi-spatial resolution for volume data
image. However, time performance could be improved                       In recent years, with the increase in GPU computing
by 3×. As Swafford et al. [114] only applied the                         power, researchers have further proposed more
tessellation method to fixed-size triangles, the results                 complex techniques to improve the efficiency of
of tessellation of much larger or smaller triangles                      volume data foveated rendering.
do not match the visual perceptual size. Zheng et                          Gallo and Placitelli [111] introduced a hybrid
al. [20] adaptively adjusted the tessellation levels                     CPU–GPU volume ray-casting system for interactive,
and culling region based on visual sensitivity. Young                    medical-quality visualization using an ordinary
and Stafford [129] adjusted the foveal region size                       desktop PC. The system combined three parts: a gaze-
and shape to correct the gaze tracing error or state                     directed volume rendering tool that renders the foveal
parameters and combined this technique with LoD                          region in maximum resolution, an inner structure
to render foveated images. Stafford and Young [130]                      tool that enables interactive inspection of data
selectively filtered the images in the peripheral region                 using two different transfer functions simultaneously,
to reduce visual artifacts owing to contrast resulting                   and a localized oversampling tool that allows
from the lower LoD before compositing foveated                           users to interactively execute oversampling and
images for presentation. Lindeberg [116] proposed a                      antialiasing techniques in the foveal region. Bruder
gaze-contingent depth of field tessellation that applies                 et al. [37] accelerated volume rendering through
tessellation to all objects within the focal plane,                      the Linde–Buzo–Gray sampling method based on
gradually decreasing tessellation levels as applied                      the visual acuity fall-off model and natural neighbor
blur increases. User studies demonstrated that this                      interpolation. Ananpiriyakul et al. [137] smoothly
technique helps reduce the number of primitives                          transited the resolution from the foveal to the

218                                                                                                      L. Wang, X. Shi, Y. Liu


peripheral region with the use of face-tracking to                      instant radiosity method that casts more VPLs to
drive adaptive-resolution volume data visualization.                    illuminate the foveal region such that more accurate
The results demonstrated a 2–2.5× frame rate                            global illumination effects in the foveal region and
improvement on interactive explorations. Kang et                        less accurate global illumination in the peripheral
al. [72] proposed a thin lens camera model to                           region can be rendered. Yang et al. [145] improved
simulate rays passing through different parts of the                    the method proposed by Wang et al. [36] and created
lens for volume data visualizations. The model                          a CMF-based perceptual probability map to manage
is implemented in the GPU pipeline with no pre-                         virtual point lights more accurately to further improve
processing. The results demonstrated that the                           rendering quality in the fovea. Because the method
method could generate volume data visualizations                        of Wang et al. [36] and Yang et al. [145] only
with better depth perception than existing DoF                          supports diffuse scenes, Shi et al. [152] adopted the
methods, and the speed was 9× faster.                                   photon mapping method to foveated rendering, which
5.6    Multi-luminance resolution                                       renders high-quality global illumination effects in the
                                                                        foveal region at interactive frame rates for the scenes
The concept of multi-luminance resolution has only                      that include diffuse, specular, glossy, and transparent
been used in foveated rendering in the past 5 years.                    materials.
  Stengel et al. [28] presented a luminance map to
adjust the sampling probability of the periphery to                     5.7   Foveated rendering for nascent data
obtain shading samples that can effectively shade                             types
important features of the image. Tursun et al. [29]                     With the rise of 3D display technologies, new data
proposed a novel luminance-contrast-aware foveated                      types appear, such as hologram data and light fields.
rendering technique that improves computational                         However, current hardware and graphic algorithms
savings by analyzing the local luminance contrast                       cannot enable high quality and low latency for 3D
of the image, this method pipeline is demonstrated                      displays. Researchers extend the foveated rendering
in Fig. 14. Wang et al. [36] proposed the foveated                      algorithms to support these nascent data types.
                                                                           Researchers extended foveated rendering methods
                                                                        from 3D geometry scenes to 4D light fields based on
                                                                        the concept of multi-spatial resolution. Sun et al.
                                                                        [121] proposed a 4D light field foveated rendering
                                                                        method with importance sampling and a sparse
                                                                        reconstruction scheme based on the spectral bounds
                                                                        and depth perception measurements. The results
                                                                        demonstrated that the technique traced only 16%–
                                                                        30% rays without compromising perceptual quality.
                                                                        Meng et al. [140] introduced a 3D-kernel foveated
                                                                        rendering method to observe light fields, which
                                                                        provided similar visual results as the original light
                                                                        fields. However, this achieves a speed improvement
                                                                        of up to 7.28× for the light fields with a resolution of
                                                                        25×25×1024×1024 p with minimal perceptual loss
                                                                        of detail.
                                                                           Foveated rendering research has also been published
Fig. 14 Luminance-contrast-aware foveated rendering proposed
                                                                        based on the concept of multi-spatial resolution
by Tursun et al. [29]. A low-resolution image was first rendered,       to improve the rendering of holograms. Wei
and then divided into multiple small patches, and subsequently, the
                                                                        and Sakamoto [128] proposed an angle-changeable
standard deviation ρ was calculated to obtain the maximum acceptable
resolution reduction for each patch. Finally, the luminance-contrast-   foveated ray tracing method for rendering the
aware adaptive resolution rendering was performed through real-time     computer-generated hologram (CGH) with better
ray tracing. Compared with standard foveated rendering, this method
achieved a 0.8–2.6× acceleration and improved perceptual quality.
                                                                        performance and almost no observable artifacts for
Reproduced with permission from Ref. [29], c ACM 2019.                  the user. Chakravarthula et al. [153] reduced the

Foveated rendering: A state-of-the-art survey                                                               219


perceived speckle noise by integrating two factors       integration into the foveated rendering paradigm to
into the phase hologram computation: (1) foveal and      improve quality and performance.
peripheral vision HVS characteristics; (2) the retinal      The development of cutting-edge foveated displays
point spread function. With this new method, the         is another potential avenue for foveated rendering.
perceived speckle noise can be pushed from the fovea     In recent years, Tan et al. [125] used beam splitters
to the periphery.                                        with different magnifications to combine two identical
                                                         displays to demonstrate a dynamic foveal VR display.
                                                         Lee et al. [135] introduced a time-multiplexed see-
6   Discussion
                                                         through fixed foveated holographic display using a
Although foveated rendering has been a focus area        beam splitter and tunable lens, with a foveal field
in research and industry for more than two decades,      of view of 1.04◦ and a peripheral field of view of
there are still many opportunities and open questions    22.6◦ . Kim et al. [134] presented a foveated display
to be solved.                                            with resolution and focal depth dynamically driven
  One potential opportunity is to take full advantage    by gaze tracking for AR. The display combines
of the human visual features for foveated rendering.     a traveling micro-display for the high-resolution
The current foveated rendering method only uses          foveal region with a wide field-of-view peripheral
parts of the HVS features, including visual acuity       display that follows the viewer’s pupil during eye
and contrast sensitivity, and other features that        movement. However, current foveated displays for
may be beneficial in this context are not reflected      VR and AR have high mechanical complexities
in existing research; therefore, further research is     and drawbacks for responsiveness and power draw.
required to investigate this. For example, visual        Focus depth estimation of current displays is
masking may be utilized for accelerating foveated        not robust; although previous research supports
rendering. This explains that the visibility of one      the feasibility of estimating focal depth based on
image, called a target, can be reduced by the presence   binocular astigmatism alone, it has also been reported
of another image, called a mask [183]. For example,      that half diopters or more are inaccurate [185]. The
as the luminance or scene changes sharply, the HVS       combination of foveated displays and prescription
sensitivity will decrease when a new scene suddenly      corrective optics also presents a challenge.
appears. Therefore, decreasing rendering quality            Based on the analysis and summary of existing
of the foveal image in the subsequent frames will        foveated rendering methods, some open questions
not cause the user to notice the difference. We          require urgent solutions.
believe that the next important step towards foveated       Currently, many studies have been published on
rendering is effectively capitalizing of human visual    foveated rendering methods for volume data and
features to achieve more aggressive foveated rendering   geometric meshes, and concepts are relatively mature.
without compromising perceptual awareness.               Only in recent years foveated rendering research
  Another potential opportunity is to apply computer     of hologram data and the light fields is nascent.
vision and artificial intelligence technologies to       Generally, foveated rendering methods involving
address some issues for current foveated rendering       volume data and geometric meshes are used for
methods. Some explorations on this aspect have been      reference, such as the ray tracing method. Thus,
completed. To further improve user gaze tracking         further research is required to identify a more suitable
accuracy, Arabadzhiyska et al. [184] proposed            foveated rendering method for these new data types.
a method to predict the landing position of the             Although the ray tracing framework can be
gaze position during saccades in foveated rendering      adopted into foveated rendering in a straightforward
preprocessing. Kaplanyan et al. [38] employed a          manner, this is inefficient for some special effects
generated adversarial neural network in the foveated     in 3D rendering, such as global illumination for
rendering post-processing stage, which reconstructed     the scene containing point light sources, and high-
details in the fovea and generated temporally stable     detailed caustics. Some rendering paradigms render
peripheral content. Other technologies, for example,     these special effects more efficiently; however, they
the attention model, could also be considered for        cannot be directly integrated into foveated rendering.

220                                                                                        L. Wang, X. Shi, Y. Liu


Adopting these rendering paradigms to support             the lack of a more general, comprehensive, and
foveated rendering is therefore a challenge. Methods      widely accepted metric has significantly complicated
proposed in Refs. [36, 145, 152] are interesting          the evaluation of foveated images/video quality. In
attempts. Based on the concept of multi-luminance         addition, constructing datasets to evaluate different
resolution, they adopt instant radiosity and photon       foveated images/video aspects could ensure improved
mapping to foveated rendering. Based on different         comparability of evaluation results.
foveation principles, many other efficient real-time         In recent years, most foveated rendering methods
rendering paradigms, such as bidirectional path           designed are for VR applications, and few methods
tracing [186] and vertex connection and merging           aim toward AR applications. Kim et al. [134]
[187], etc., can be applied to foveated rendering for     investigated foveated rendering under AR. The
improved performance.                                     focus was predominantly on the design of a
  To evaluate foveated images/video quality, the          dynamically-foveated augmented reality display. For
straightforward method is to design perceptual            AR applications that require virtual and real fusion,
experiments to collect user’s perception information.     the degree of fusion will directly affect the quality
As perceptual experiments are typically time-             of rendering results; therefore, the question of how
consuming and costly, they should be performed for        to control the degree of fusion to generate images of
methods with a greater chance of success. Therefore,      different qualities in different regions remains an open
some objective metrics based on the biological and        challenge. For information-enhanced AR applications,
physical theories involving foveated rendering must       it is also worth exploring whether relevant content
be proposed to quickly evaluate the feasibility of the    such as scene semantic and task target information
tested foveated rendering methods. Currently, some        can be added to foveated rendering.
metrics exist to evaluate foveated image quality, for        In addition to improving rendering speed, foveated
example: (1) The foveal signal-to-noise ratio (FSNR)      rendering can also be used to complete specific
[188] valued the distortion between foveated images       tasks. For example, Joshi and Poullis [139] presented
and reference images with a weighted signal-to-noise      foveated rendering-based redirected walking in VR,
ratio. FSNR failed to consider user perception of         which rendered a high-quality region to guide the
foveated images quality, which may cause perceptual       spatially-varying rotation and updated peripheral
deviations in evaluating foveated images. (2) The         framebuffer during inattentional blindness. Whether
foveated wavelet image quality index (FWQI) [189]         foveated rendering can assist or improve other VR
calculated the wavelet coefficient difference between     and AR tasks is yet to be explored.
foveated and reference images with the integration of
spatial CSF. FWQI did not consider spatio-temporal        7   Conclusions
CSF while it was reported that the contrast sensitivity
of the HVS can be significantly influenced by the         This paper surveys research and development
retinal velocity [190]. (3) The foveated mean squared     involving foveated rendering over the past 31
error (FMSE) [191] evaluated foveated video quality       years. Visual perception theories and taxonomies
with the consideration of both spatial and spatio-        regarding foveated rendering are discussed in-depth.
temporal CSF. FMSE assumed that eye fixation              We respectively review early foveated rendering
points are always located at the center of images.        technologies (from 1990 to 2011) and those that
This assumption potentially introduces biases in          have more recently emerged over the past decade
evaluating visual quality. (4) The window-based           (from 2012 to 2021). Finally, we discuss potential
structural similarity index (WSSIM) [192] used            opportunities and open questions for future research
different rules to evaluate foveated image quality        in this field.
for different windows on the foveated images, the
scoring rules for the window closer to the fovea          Acknowledgements
will be more stringent. WSSIM relies on selecting         This work was supported by National Key
an appropriate saliency model. However, this may          R&D Program of China (2019YFC1521102), the
bias foveated image evaluation results. Thus far,         National Natural Science Foundation of China

Foveated rendering: A state-of-the-art survey                                                                             221


(61932003), and Beijing Science and Technology Plan                [12] Saint-Louis, C.; Hamam, A. Survey of haptic
(Z221100007722004).                                                     technology and entertainment applications. In:
                                                                        Proceedings of the SoutheastCon, 1–7, 2021.
Declaration of competing interest                                  [13] Puggioni, M. P.; Frontoni, E.; Paolanti, M.; Pierdicca,
                                                                        R.; Malinverni, E. S.; Sasso, M. A content creation
The authors have no competing interests to declare
                                                                        tool for AR/VR applications in education: The
that are relevant to the content of this article.
                                                                        ScoolAR framework. In: Augmented Reality, Virtual
                                                                        Reality, and Computer Graphics. Lecture Notes in
References
                                                                        Computer Science, Vol. 12243. De Paolis, L.; Bourdot,
  [1] Corrêa, C. G.; Nunes, F. L. S.; Bezerra, A.; Carvalho,           P. Eds. Springer Cham, 205–219, 2020.
      P. M. Evaluation of VR medical training applications         [14] Ferdani, D.; Fanini, B.; Piccioli, M. C.; Carboni, F.;
      under the focus of professionals of the health area.              Vigliarolo, P. 3D reconstruction and validation of
      In: Proceedings of the ACM Symposium on Applied                   historical background for immersive VR applications
      Computing, 821–825, 2009.                                         and games: The case study of the Forum of Augustus
  [2] Hsieh, M. C.; Lin, Y. H. VR and AR applications in                in Rome. Journal of Cultural Heritage Vol. 43, 129–
      medical practice and education. Hu Li Za Zhi Vol. 64,             143, 2020.
      No. 6, 12–18, 2017.                                          [15] Tanenbaum, T. J.; Hartoonian, N.; Bryan, J. “How
  [3] Hsieh, M. C.; Lee, J.-J. Preliminary study of VR and              do I make this thing smile?”: An inventory of
      AR applications in medical and healthcare education.              expressive nonverbal communication in commercial
      Journal of Nursing and Health Studies Vol. 3, No. 1,              social virtual reality platforms. In: Proceedings of
      1, 2018.                                                          the CHI Conference on Human Factors in Computing
                                                                        Systems, 1–13, 2020.
  [4] Rizzo, A.; Morie, J. F.; Williams, J.; Pair, J.;
                                                                   [16] Potter, M. C.; Wyble, B.; Hagmann, C. E.; McCourt,
      Buckwalter, J. G. Human emotional state and its
                                                                        E. S. Detecting meaning in RSVP at 13 ms per picture.
      relevance for military VR training. In: Proceedings
                                                                        Attention, Perception, & Psychophysics Vol. 76, No. 2,
      of the 11th International Conference on Human
                                                                        270–279, 2014.
      Computer Interaction, 2005.
                                                                   [17] Hendrickson, A. E.; Yuodelis, C. The morphological
  [5] Lele, A. Virtual reality and its military utility. Journal
                                                                        development of the human fovea. Ophthalmology
      of Ambient Intelligence and Humanized Computing
                                                                        Vol. 91, No. 6, 603–612, 1984.
      Vol. 4, No. 1, 17–26, 2013.
                                                                   [18] Loschky, L. C.; McConkie, G. W.; Yang, J.;
  [6] Ahir, K.; Govani, K.; Gajera, R.; Shah, M.
                                                                        Miller, M. E. Perceptual effects of a gaze-contingent
      Application on virtual reality for enhanced education
                                                                        multi-resolution display based on a model of
      learning, military training and sports. Augmented
                                                                        visual sensitivity. In: Proceedings of the ARL
      Human Research Vol. 5, No. 1, 7, 2020.
                                                                        Federated Laboratory 5th Annual Symposium-ADID
  [7] Ong, S. K.; Nee, A. Y. C. Virtual and Augmented                   Consortium, 53–58, 2001.
      Reality Applications in Manufacturing. London:               [19] Luebke, D.; Hallen, B. Perceptually driven
      Springer London, 2004.                                            simplification for interactive rendering. In: Rendering
  [8] Choi, S.; Jung, K.; Do Noh, S. Virtual reality                    Techniques 2001. Eurographics. Gortler, S. J.;
      applications in manufacturing industries: Past                    Myszkowski, K. Eds. Springer Vienna, 223–234, 2001.
      research, present findings, and future directions.           [20] Zheng, Z. P.; Yang, Z.; Zhan, Y. W.; Li, Y. Q.;
      Concurrent Engineering Vol. 23, No. 1, 40–63, 2015.               Yu, W. X. Perceptual model optimized efficient
  [9] Doolani, S.; Wessels, C.; Kanal, V.; Sevastopoulos, C.;           foveated rendering. In: Proceedings of the 24th
      Jaiswal, A.; Nambiappan, H.; Makedon, F. A review of              ACM Symposium on Virtual Reality Software and
      extended reality (XR) technologies for manufacturing              Technology, 1–2, 2018.
      training. Technologies Vol. 8, No. 4, 77, 2020.              [21] Schütz, M.; Krösl, K.; Wimmer, M. Real-time
 [10] Avila, L.; Bailey, M. Virtual reality for the masses.             continuous level of detail rendering of point clouds.
      IEEE Computer Graphics and Applications Vol. 34,                  In: Proceedings of the IEEE Conference on Virtual
      No. 5, 103–104, 2014.                                             Reality and 3D User Interfaces, 103–110, 2019.
 [11] Bialkova, S.; Van Gisbergen, M. S. When sound                [22] Loschky, L. C.; McConkie, G. W. User performance
      modulates vision: VR applications for art and                     with gaze contingent multiresolutional displays. In:
      entertainment. In: Proceedings of the IEEE 3rd                    Proceedings of the Symposium on Eye Tracking
      Workshop on Everyday Virtual Reality, 1–6, 2017.                  Research & Applications, 97–103, 2000.

222                                                                                                L. Wang, X. Shi, Y. Liu


 [23] Parkhurst, D. J.; Niebur, E. Variable-resolution          [36] Wang, L. L.; Li, R. Z.; Shi, X. H.; Yan, L. Q.; Li,
      displays: A theoretical, practical, and behavioral             Z. C. Foveated instant radiosity. In: Proceedings of
      evaluation. Human Factors Vol. 44, No. 4, 611–629,             the IEEE International Symposium on Mixed and
      2002.                                                          Augmented Reality, 1–11, 2020.
 [24] Duchowski, A. T.; House, D. H.; Gestring, J.; Wang,       [37] Bruder, V.; Schulz, C.; Bauer, R.; Frey, S.; Weiskopf,
      R. I.; Krejtz, K.; Krejtz, I.; Mantiuk, R.; Bazyluk, B.        D.; Ertl, T. Voronoi-based foveated volume rendering.
      Reducing visual discomfort of 3D stereoscopic displays         In: EuroVis 2019 - Short Papers. Johansson, J.; Sadlo,
      with gaze-contingent depth-of-field. In: Proceedings of        F.; Marai, G. E. Eds. The Eurographics Association,
      the ACM Symposium on Applied Perception, 39–46,                2019.
      2014.                                                     [38] Kaplanyan, A. S.; Sochenov, A.; Leimkühler, T.;
 [25] Turner, E.; Jiang, H. M.; Saint-Macary, D.; Bastani,           Okunev, M.; Goodall, T.; Rufo, G. DeepFovea:
      B. Phase-aligned foveated rendering for virtual reality        Neural reconstruction for foveated rendering and video
      headsets. In: Proceedings of the IEEE Conference on            compression using learned statistics of natural videos.
      Virtual Reality and 3D User Interfaces, 1–2, 2018.             ACM Transactions on Graphics Vol. 38, No. 6, Article
 [26] Guenter, B.; Finch, M.; Drucker, S.; Tan, D.; Snyder,          No. 212, 2019.
      J. Foveated 3D graphics. ACM Transactions on              [39] Weier, M.; Stengel, M.; Roth, T.; Didyk, P.;
      Graphics Vol. 31, No. 6, Article No. 164, 2012.                Eisemann, E.; Eisemann, M.; Grogorick, S.;
 [27] Bastani, B.; Funt, B.; Vignaud, S.; Jiang, H. Smoothly         Hinkenjann, A.; Kruijff, E.; Magnor, M.; et al.
      varying foveated rendering. US Patent 10,546,364,              Perception-driven accelerated rendering. Computer
      2020.                                                          Graphics Forum Vol. 36, No. 2, 611–643, 2017.
 [28] Stengel, M.; Grogorick, S.; Eisemann, M.; Magnor, M.      [40] Cline, D. Dictionary of Visual Science. Chilton Book
      Adaptive image-space sampling for gaze-contingent              Company, 1980.
      real-time rendering. Computer Graphics Forum              [41] Ivančić Valenko, S.; Cviljušac, V.; Modrić, D. The
      Vol. 35, No. 4, 129–139, 2016.                                 impact of physical parameters on the perception of
 [29] Tursun, O. T.;          Arabadzhiyska-Koleva, E.;              the moving elements in peripheral part of the screen.
      Wernikowski, M.; Mantiuk, R.; Seidel, H. P.;                   Tehnički vjesnik Vol. 26 No. 5, 1444–1450, 2019.
      Myszkowski, K.; Didyk, P. Luminance-contrast-aware        [42] Schaadt, A. K. Disorders of binocular convergent
      foveated rendering. ACM Transactions on Graphics               fusion and stereoscopic space perception following
      Vol. 38, No. 4, Article No. 98, 2019.                          acquired brain damage: Treatment and neuro-
 [30] Tavakoli, M.; Khan, M.; Renschler, M.; Mondal, M.              anatomical implications. Dissertation. Universität des
      Scene-based foveated rendering of graphics content.            Saarlandes, 2015.
      US Patent 10,482,648, 2019.                               [43] Strasburger, H.; Rentschler, I.; Jüttner, M. Peripheral
 [31] Koskela, M.; Viitanen, T.; Jääskeläinen, P.; Takala,        vision and pattern recognition: A review. Journal of
      J. Foveated path tracing. In: Advances in Visual               Vision Vol. 11, No. 5, 13, 2011.
      Computing. Lecture Notes in Computer Science, Vol.        [44] Fender, D.; Julesz, B. Extension of panum’s fusional
      10072. Springer Cham, 723–732, 2016.                           area in binocularly stabilized vision. Journal of the
 [32] Molenaar, E. N. Towards real-time ray tracing through          Optical Society of America Vol. 57, No. 6, 819–830,
      foveated rendering. Master Thesis. University of               1967.
      Utrecht, 2018.                                            [45] Georgeson, M. A.; Wallis, S. A. Binocular
 [33] Koskela, M.; Lotvonen, A.; Mäkitalo, M.; Kivi, P.;            fusion, suppression and diplopia for blurred edges.
      Viitanen, T.; Jääskeläinen, P. Foveated real-time           Ophthalmic and Physiological Optics Vol. 34, No. 2,
      path tracing in visual-polar space. In: Eurographics           163–185, 2014.
      Symposium on Rendering - DL-only and Industry             [46] Porac, C.; Coren, S. The dominant eye. Psychological
      Track. Boubekeur, T.; Sen, P. Eds. The Eurographics            Bulletin Vol. 83, No. 5, 880–897, 1976.
      Association, 2019.                                        [47] Robson, J. G. Spatial and temporal contrast-
 [34] Koskela, M. Foveated path tracing with fast                    sensitivity functions of the visual system. Journal
      reconstruction and efficient sample distribution.              of the Optical Society of America Vol. 56, No. 8, 1141–
      Dissertation. Dissertation. Tampere University, 2020.          1142, 1966.
 [35] Levoy, M.; Whitaker, R. Gaze-directed volume              [48] Campbell, F. W.; Robson, J. G. Application of Fourier
      rendering. In: Proceedings of the Symposium on                 analysis to the visibility of gratings. The Journal of
      Interactive 3D Graphics, 217–223, 1990.                        Physiology Vol. 197, No. 3, 551–566, 1968.

Foveated rendering: A state-of-the-art survey                                                                           223


 [49] Kelly, D. H. Motion and vision. II. Stabilized spatio-          Pérard-Gayot, A.; Slusallek, P.; Li, Y. Foveated real-
      temporal threshold surface. Journal of the Optical              time ray tracing for head-mounted displays. Computer
      Society of America Vol. 69, No. 10, 1340–1349, 1979.            Graphics Forum Vol. 35, No. 7, 289–298, 2016.
 [50] Mullen, K. T. The contrast sensitivity of human colour      [63] Mikkola, M.; Boev, A.; Gotchev, A. Relative
      vision to red-green and blue-yellow chromatic gratings.          importance of depth cues on portable autostereoscopic
      The Journal of Physiology Vol. 359, No. 1, 381–400,              display. In: Proceedings of the 3rd Workshop on
      1985.                                                            Mobile Video Delivery, 63–68, 2010.
 [51] Geisler, W.; Perry, J. Real-time foveated multiresolution   [64] Panum, P. L. Physiologische Untersuchungen über das
      system for low-bandwidth video communication. In:                Sehen mit zwei Augen. Schwer, 1858.
      Proceedings of the SPIE 3299, Human Vision and              [65] Mitchell, D. E. A review of the concept of “panum’s
      Electronic Imaging III, 294–305, 1998.                           fusional areas”. Optometry and Vision Science Vol.
 [52] Krajancich, B.; Kellnhofer, P.; Wetzstein, G. A                  43, No. 6, 387–401, 1966.
      perceptual model for eccentricity-dependent spatio-         [66] Hillaire, S.; Lecuyer, A.; Cozot, R.; Casiez, G.
      temporal flicker fusion and its applications to foveated         Using an eye-tracking system to improve camera
      graphics. ACM Transactions on Graphics Vol. 40, No.              motions and depth-of-field blur effects in virtual
      4, Article No. 47, 2021.                                         environments. In: Proceedings of the IEEE Virtual
 [53] Weymouth, F. W. Visual sensory units and the                     Reality Conference, 47–50, 2008.
      minimal angle of resolution. American Journal of            [67] Mantiuk, R.; Bazyluk, B.; Tomaszewska, A. Gaze-
      Ophthalmology Vol. 46, No. 1, 102–113, 1958.                     dependent depth-of-field effect rendering in virtual
 [54] Weymouth, F. W. Visual sensory units and the                     environments. In: Serious Games Development and
      minimum angle of resolution. Optometry and Vision                Applications. Lecture Notes in Computer Science,
      Science Vol. 40, No. 9, 550–568, 1963.                           Vol. 6944. Ma, M.; Fradinho Oliveira, M.; Madeiras
 [55] Daniel, P. M.; Whitteridge, D. The representation                Pereira, J. Eds. Springer Berlin Heidelberg, 1–12,
      of the visual field on the cerebral cortex in monkeys.           2011.
      The Journal of Physiology Vol. 159, No. 2, 203–221,         [68] Vinnikov, M.; Allison, R. S. Gaze-contingent depth
      1961.                                                            of field in realistic scenes: The user experience. In:
 [56] Levi, D. M.; Klein, S. A.; Aitsebaomo, A. P. Vernier             Proceedings of the Symposium on Eye Tracking
      acuity, crowding and cortical magnification. Vision              Research and Applications, 119–126, 2014.
      Research Vol. 25, No. 7, 963–977, 1985.                     [69] Mauderer, M.; Conte, S.; Nacenta, M. A.; Vishwanath,
 [57] Nakayama, K. Properties of early motion processing:              D. Depth perception with gaze-contingent depth of
      Implications for the sensing of egomotion. In:                   field. In: Proceedings of the SIGCHI Conference on
      Perception and Control of Self-motion. Psychology                Human Factors in Computing Systems, 217–226, 2014.
      Press, 93–104, 1990.                                        [70] Gupta, K.; Kazi, S. Gaze contingent depth of field
 [58] Ohshima, T.; Yamamoto, H.; Tamura, H. Gaze-                      display. 2016. Available at http://stanford.edu/class/
      directed adaptive rendering for interacting with                 ee367/Winter2016/Gupta Kazi Report.pdf.
      virtual space. In: Proceedings of the IEEE Virtual          [71] Weier, M.; Roth, T.; Hinkenjann, A.; Slusallek,
      Reality Annual International Symposium, 103–110,                 P. Foveated depth-of-field filtering in head-mounted
      2002.                                                            displays. ACM Transactions on Applied Perception
 [59] Luebke, D.; Hallen, B.; Newfield, D.; Watson, B.                 Vol. 15, No. 4, Article No. 26, 2018.
      Perceptually driven simplification using gaze-directed      [72] Kang, J.; Lee, J.; Shin, Y. G.; Kim, B. Depth-of-field
      rendering. Technical Report CS-2000-04. Department               rendering using progressive lens sampling in direct
      of Computer Science, University of Virginia, 2000.               volume rendering. IEEE Access Vol. 8, 93335–93345,
 [60] Parkhurst, D.; Law, I.; Niebur, E. Evaluating                    2020.
      gaze-contingent level of detail rendering of virtual        [73] Shneor, E.; Hochstein, S. Eye dominance effects in
      environments using visual search. 2001.                          feature search. Vision Research Vol. 46, No. 25, 4258–
 [61] Vaidyanathan, K.; Salvi, M.; Toth, R.; Foley,                    4269, 2006.
      T.; Akenine-Möller, T.; Nilsson, J.; Munkberg, J.;         [74] Koçtekin B.; Gündoğan, N. Ü.; Altıntaş, A. G. K.;
      Hasselgren, J.; Sugihara, M.; Clarberg, P.; et al.               Yazıcı, A. C. Relation of eye dominancy with color
      Coarse pixel shading. In: Proceedings of the High                vision discrimination performance ability in normal
      Performance Graphics, 9–18, 2014.                                subjects. International Journal of Ophthalmology
 [62] Weier, M.; Roth, T.; Kruijff, E.; Hinkenjann, A.;                Vol. 6, No. 5, 733–738, 2013.

224                                                                                                   L. Wang, X. Shi, Y. Liu


 [75] Meng, X. X.; Du, R. F.; Varshney, A. Eye-dominance-         [89] Liu, Y. M.; Jiang, B. C. Contrast sensitivity measured
      guided foveated rendering. IEEE Transactions on                  during smooth pursuit movement. Science China
      Visualization and Computer Graphics Vol. 26, No.                 Chemistry Vol. 27, No. 7, 710–721, 1984.
      5, 1972–1980, 2020.                                         [90] Flipse, J. P.; Wildt, G. J. V. D.; Rodenburg, M.;
 [76] Owsley, C. Contrast sensitivity. Ophthalmology Clinics           Keemink, C. J.; Knol, P. G. M. Contrast sensitivity
      of North America Vol. 16, No. 2, 171–177, 2003.                  for oscillating sine wave gratings during ocular fixation
 [77] Kim, K. J.; Mantiuk, R.; Lee, K. H. Measurements                 and pursuit. Vision Research Vol. 28, No. 7, 819–826,
      of achromatic and chromatic contrast sensitivity                 1988.
      functions for an extended range of adaptation               [91] Van Meeteren, A.; Vos, J. J. Resolution and contrast
      luminance. In: Proceedings of the SPIE 8651, Human               sensitivity at low luminances. Vision Research Vol.
      Vision and Electronic Imaging XVIII, 86511A, 2013.               12, No. 5, 825–833, 1972.
 [78] Chwesiuk, M.; Mantiuk, R. Measurements of contrast          [92] Mullen, K. T. Colour vision as a post-receptoral
      sensitivity for peripheral vision. In: Proceedings of            specialization of the central visual field. Vision
      the ACM Symposium on Applied Perception, 1–9,                    Research Vol. 31, No. 1, 119–130, 1991.
      2019.                                                       [93] Anderson, S. J.; Mullen, K. T.; Hess, R. F. Human
 [79] Tyler, C. W.; Hamer, R. D. Analysis of visual                    peripheral spatial resolution for achromatic and
      modulation sensitivity. IV. Validity of the Ferry-Porter         chromatic stimuli: Limits imposed by optical and
      law. Journal of the Optical Society of America A Vol. 7,         retinal factors. The Journal of Physiology Vol. 442,
      No. 4, 743–758, 1990.                                            No. 1, 47–64, 1991.
 [80] Watson, A. B. Visual detection of spatial contrast          [94] Mullen, K. T.; Kingdom, F. A. A. Differential
      patterns: Evaluation of five simple models. Optics               distributions of red-green and blue-yellow cone
      Express Vol. 6, No. 1, 12–33, 2000.                              opponency across the visual field. Visual Neuroscience
 [81] Yee, H.; Pattanaik, S.; Greenberg, D. P.                         Vol. 19, No. 1, 109–118, 2002.
      Spatiotemporal sensitivity and visual attention for         [95] Mullen, K. T.; Sakurai, M.; Chu, W. Does L/M cone
      efficient rendering of dynamic environments. ACM                 opponency disappear in human periphery? Perception
      Transactions on Graphics Vol. 20, No. 1, 39–65, 2001.            Vol. 34, No. 8, 951–959, 2005.
 [82] Westland, S.; Owens, H.; Cheung, V.; Paterson-              [96] Duchowski, A. T.;       Çöltekin, A. Foveated
      Stephens, I. Model of luminance contrast-sensitivity             gaze-contingent displays for peripheral LOD
      function for application to image assessment. Color              management, 3D visualization, and stereo imaging.
      Research & Application Vol. 31, No. 4, 315–319, 2006.            ACM Transactions on Multimedia Computing,
 [83] Fairchild, M. D. Color Appearance Models. John                   Communications, and Applications Vol. 3, No. 4,
      Wiley & Sons, 2013.                                              Article No. 6, 2007.
 [84] Schade, O. H. Optical and photoelectric analog of the       [97] Tyler, C. W.; Hamer, R. D. Eccentricity and the ferry-
      eye. Journal of the Optical Society of America Vol.              porter law. Journal of the Optical Society of America
      46, No. 9, 721–739, 1956.                                        A Vol. 10, No. 9, 2084–2087, 1993.
 [85] Xia, J. C.; Varshney, A. Dynamic view-dependent             [98] Spjut, J.; Boudaoud, B.; Kim, J.; Greer, T.; Albert,
      simplification for polygonal models. In: Proceedings             R.; Stengel, M.; Aksit, K.; Luebke, D. Toward
      of the 7th Annual IEEE Visualization, 327–334, 2009.             standardized classification of foveated displays. IEEE
 [86] Hoppe, H. View-dependent refinement of progressive               Transactions on Visualization and Computer Graphics
      meshes. In: Proceedings of the 24th Annual                       Vol. 26, No. 5, 2126–2134, 2020.
      Conference on Computer Graphics and Interactive             [99] Duchowski, A. T.; Bate, D.; Stringfellow, P.;
      Techniques, 189–198, 1997.                                       Thakur, K.; Melloy, B. J.; Gramopadhye, A. K. On
 [87] Luebke, D.; Erikson, C. View-dependent simplification            spatiochromatic visual sensitivity and peripheral color
      of arbitrary polygonal environments. In: Proceedings             LOD management. ACM Transactions on Applied
      of the 24th Annual Conference on Computer Graphics               Perception Vol. 6, No. 2, Article No. 9, 2009.
      and Interactive Techniques, 199–208, 1997.                 [100] Funkhouser, T. A.; Séquin, C. H. Adaptive
 [88] Patney, A.; Salvi, M.; Kim, J.; Kaplanyan, A.;                   display algorithm for interactive frame rates during
      Wyman, C.; Benty, N.; Luebke, D.; Lefohn, A.                     visualization of complex virtual environments. In:
      Towards foveated rendering for gaze-tracked virtual              Proceedings of the 20th Annual Conference on
      reality. ACM Transactions on Graphics Vol. 35, No. 6,            Computer Graphics and Interactive Techniques, 247–
      Article No. 179, 2016.                                           254, 1993.

Foveated rendering: A state-of-the-art survey                                                                             225


[101] Reddy, M. Perceptually optimized 3D graphics. IEEE         [114] Swafford, N. T.; Iglesias-Guitian, J. A.; Koniaris,
      Computer Graphics and Applications Vol. 21, No. 5,               C.; Moon, B.; Cosker, D.; Mitchell, K. User, metric,
      68–75, 2001.                                                     and computational evaluation of foveated rendering
[102] Murphy, H.; Duchowski, A. T. Gaze-contingent                     methods. In: Proceedings of the ACM Symposium on
      level of detail rendering. In: Proceedings of the                Applied Perception, 7–14, 2016.
      Eurographics 2001 - Short Presentations, 2001.             [115] Pai, Y. S.; Tag, B.; Outram, B.; Vontin, N.; Sugiura,
[103] Cheng, I. Foveated 3D model simplification. In:                  K.; Kai, K. Z. GazeSim: Simulating foveated rendering
      Proceedings of the 7th International Symposium on                using depth in eye gaze for VR. In: Proceedings of the
      Signal Processing and Its Applications, 241–244, 2003.           ACM SIGGRAPH Posters, 1–2, 2016.
[104] Duchowski, A. T.; Cournia, N.; Murphy, H. Gaze-            [116] Lindeberg, T. Concealing rendering simplifications
      contingent displays: Review and current trends. 2004.            using gaze contingent depth of field. Master Thesis.
      Available at http://andrewd.ces.clemson.edu/gcd/                 KTH Royal Institute of Technology, 2016.
      adc04.pdf.                                                 [117] Albert, R.; Patney, A.; Luebke, D.; Kim, J. Latency
[105] Reingold, E. M.; Loschky, L. C.; McConkie, G. W.;                requirements for foveated rendering in virtual reality.
      Stampe, D. M. Gaze-contingent multiresolutional                  ACM Transactions on Applied Perception Vol. 14,
      displays: An integrative review. Human Factors Vol.              No. 4, Article No. 25, 2017.
      45, No. 2, 307–328, 2003.                                  [118] Blackmon, S.; Peterson, L. T.; Ozdas, C.; Clohset, S.
[106] Zhou, J. L.; Döring, A.; Tönnies, K. D. Distance based         J. Foveated rendering. US Patent App. 15/372,589,
      enhancement for focal region based volume rendering.             2017.
      In: Bildverarbeitung für die Medizin 2004. Informatik     [119] Koskela, M.; Immonen, K.; Viitanen, T.; Jääskeläinen,
      aktuell. Tolxdorff, T.; Braun, J.; Handels, H.; Horsch,          P.; Multanen, J.; Takala, J. Foveated instant preview
      A.; Meinzer, H. P. Eds. Springer Berlin Heidelberg,              for progressive rendering. In: Proceedings of the
      199–203, 2004.                                                   SIGGRAPH Asia Technical Briefs, 1–4, 2017.
[107] Yu, H.; Chang, E. C.; Huang, Z. Y.; Zheng, Z. J.           [120] Hsu, C. F.; Chen, A.; Hsu, C. H.; Huang, C.
      Fast rendering of foveated volumes in wavelet-based              Y.; Lei, C. L.; Chen, K. T. Is foveated rendering
      representation. The Visual Computer Vol. 21, No. 8,              perceivable in virtual reality? Exploring the efficiency
      735–744, 2005.                                                   and consistency of quality assessment methods.
[108] Lu, A. D.; Maciejewski, R.; Ebert, D. Volume                     In: Proceedings of the 25th ACM International
      composition using eye tracking data. In: Proceedings             Conference on Multimedia, 55–63, 2017.
      of the 8th Joint Eurographics/IEEE VGTC                    [121] Sun, Q.; Huang, F. C.; Kim, J.; Wei, L. Y.; Luebke,
      Conference on Visualization, 115–122, 2006.                      D.; Kaufman, A. Perceptually-guided foveation for
[109] Hillaire, S.; Lécuyer, A.; Cozot, R.; Casiez, G. Depth-         light field displays. ACM Transactions on Graphics
      of-field blur effects for first-person navigation in             Vol. 36, No. 6, Article No. 192, 2017.
      virtual environments. IEEE Computer Graphics and           [122] Lungaro, P.; Sjoberg, R.; Valero, A. J. F.; Mittal,
      Applications Vol. 28, No. 6, 47–55, 2008.                        A.; Tollmar, K. Gaze-aware streaming solutions for
[110] Murphy, H. A.; Duchowski, A. T.; Tyrrell, R. A.                  the next generation of mobile VR experiences. IEEE
      Hybrid image/model-based gaze-contingent rendering.              Transactions on Visualization and Computer Graphics
      ACM Transactions on Applied Perception Vol. 5, No.               Vol. 24, No. 4, 1535–1544, 2018.
      4, Article No. 22, 2009.                                   [123] Meng, X. X.; Du, R. F.; Zwicker, M.; Varshney, A.
[111] Gallo, L.; Placitelli, A. P. High-fidelity visualization         Kernel foveated rendering. Proceedings of the ACM on
      of large medical datasets on commodity hardware.                 Computer Graphics and Interactive Techniques Vol. 1,
      ISRN Biomedical Engineering Vol. 2013, Article ID                No. 1, Article No. 5, 2018.
      892967, 2013.                                              [124] Koskela, M. K.; Immonen, K. V.; Viitanen, T. T.;
[112] Fujita, M.; Harada, T. Foveated real-time ray tracing            Jääskeläinen, P. O.; Multanen, J. I.; Takala, J. H.
      for virtual reality headset. In: Proceedings of the              Instantaneous foveated preview for progressive Monte
      SIGGRAPH Asia, 2014.                                             Carlo rendering. Computational Visual Media Vol. 4,
[113] Patney, A.; Kim, J.; Salvi, M.; Kaplanyan, A.;                   No. 3, 267–276, 2018.
      Wyman, C.; Benty, N.; Lefohn, A.; Luebke,                  [125] Tan, G. J.; Lee, Y. H.; Zhan, T.; Yang, J. L.; Liu, S.;
      D. Perceptually-based foveated virtual reality. In:              Zhao, D. F.; Wu, S. T. Foveated imaging for near-eye
      Proceedings of the ACM SIGGRAPH Emerging                         displays. Optics Express Vol. 26, No. 19, 25076–25085,
      Technologies, 1–2, 2016.                                         2018.

226                                                                                                  L. Wang, X. Shi, Y. Liu


[126] Wilson, A.; Lanman, D. R.; Trail, N. D.; McEldowney,             ACM Transactions on Graphics Vol. 39, No. 2, Article
      S. C.; McNally, S. J.; Sulai, Y. N. B. Rendering                 No. 10, 2020.
      composite content on a head mounted display                 [139] Joshi, Y.; Poullis, C. Inattentional blindness for
      including a high resolution inset. US Patent 9,972,071,           redirected walking using dynamic foveated rendering.
      2018.                                                             IEEE Access Vol. 8, 39013–39024, 2020.
[127] Young, A.; Ho, C.; Stafford, J. R. Foveal adaptation        [140] Meng, X. X.; Du, R. F.; JaJa, J. F.; Varshney, A.
      of particles and simulation models in a foveated                  3D-kernel foveated rendering for light fields. IEEE
      rendering system. US Patent 10,339,692, 2019.                     Transactions on Visualization and Computer Graphics
[128] Wei, L. J.; Sakamoto, Y. Fast calculation method                  Vol. 27, No. 8, 3350–3360, 2021.
      with foveated rendering for computer-generated              [141] Frieß, F.; Braun, M.; Bruder, V.; Frey, S.; Reina, G.;
      holograms using an angle-changeable ray-tracing                   Ertl, T. Foveated encoding for large high-resolution
      method. Applied Optics Vol. 58, No. 5, A258–A266,                 displays. IEEE Transactions on Visualization and
      2019.                                                             Computer Graphics Vol. 27, No. 2, 1850–1859, 2021.
[129] Young, A.; Stafford, J. R. Real-time user adaptive          [142] Yoo, C.; Xiong, J. H.; Moon, S.; Yoo, D.; Lee, C. K.;
      foveated rendering. US Patent 10,192,528, 2019.                   Wu, S. T.; Lee, B. Foveated display system based on
[130] Stafford, J. R.; Young, A. Selective peripheral vision            a doublet geometric phase lens. Optics Express Vol.
      filtering in a foveated rendering system. US Patent               28, No. 16, 23690–23702, 2020.
      10,169,846, 2019.                                           [143] Bitterli, B.; Wyman, C.; Pharr, M.; Shirley, P.;
[131] Friston, S.; Ritschel, T.; Steed, A. Perceptual                   Lefohn, A.; Jarosz, W. Spatiotemporal reservoir
      rasterization for head-mounted display image                      resampling for real-time ray tracing with dynamic
      synthesis. ACM Transactions on Graphics Vol. 38,                  direct lighting. ACM Transactions on Graphics
      No. 4, Article No. 97, 2019.                                      Vol. 39, No. 4, Article No. 148, 2020.
[132] Radkowski, R.; Raul, S. Impact of foveated rendering        [144] Deza, A.; Konkle, T. Emergent properties of foveated
      on procedural task training. In: Virtual, Augmented               perceptual systems. arXiv preprint arXiv:2006.07991,
      and Mixed Reality. Multimodal Interaction. Lecture                2020.
      Notes in Computer Science, Vol. 11574. Chen, J.;            [145] Yang, Q. Q.; Chen, Z. X.; Liu, Y. L.; Xing, G. Y.;
      Fragomeni, G. Eds. Springer Cham, 258–267, 2019.                  Zhang, Y. C. Foveated light culling. Computers &
[133] Siekawa, A.; Chwesiuk, M.; Mantiuk, R.; Piórkowski,              Graphics Vol. 97, 200–207, 2021.
      R. Foveated ray tracing for VR headsets. In:                [146] Franke, L.; Fink, L.; Martschinke, J.; Selgrad, K.;
      MultiMedia Modeling. Lecture Notes in Computer                    Stamminger, M. Time-warped foveated rendering for
      Science, Vol. 11295. Kompatsiaris, I.; Huet, B.;                  virtual reality headsets. Computer Graphics Forum
      Mezaris, V.; Gurrin, C.; Cheng, W. H.; Vrochidis,                 Vol. 40, No. 1, 110–123, 2021.
      S. Eds. Springer Cham, 106–117, 2018.                       [147] Surace, L.; Wernikowski, M.; Tursun, C.; Myszkowski,
[134] Kim, J.; Jeong, Y.; Stengel, M.; Akşit, K.; Albert,              K.; Mantiuk, R.; Didyk, P. Learning foveated
      R.; Boudaoud, B.; Greer, T.; Kim, J.; Lopes, W.;                  reconstruction to preserve perceived image statistics.
      Majercik, Z.; et al. Foveated AR. ACM Transactions                arXiv preprint arXiv:2108.03499, 2021.
      on Graphics Vol. 38, No. 4, Article No. 99, 2019.           [148] Kim, Y.; Ko, Y.; Ihm, I. Selective foveated ray
[135] Lee, J. S.; Kim, Y. K.; Lee, M. Y.; Won, Y.                       tracing for head-mounted displays. In: Proceedings
      H. Enhanced see-through near-eye display using                    of the IEEE International Symposium on Mixed and
      time-division multiplexing of a Maxwellian-view and               Augmented Reality, 413–421, 2021.
      holographic display. Optics Express Vol. 27, No. 2,         [149] Liu, J. Y.; Mantel, C.; Forchhammer, S. Perception-
      689–701, 2019.                                                    driven hybrid foveated depth of field rendering for
[136] Young, A.; Ho, C.; Stafford, J. R. Optimized shadows              head-mounted displays. In: Proceedings of the IEEE
      in a foveated rendering system. US Patent 10,650,544,             International Symposium on Mixed and Augmented
      2020.                                                             Reality, 1–10, 2021.
[137] Ananpiriyakul, T.; Anghel, J.; Potter, K.; Joshi, A. A      [150] Walton, D. R.; Dos Anjos, R. K.; Friston, S.; Swapp,
      gaze-contingent system for foveated multiresolution               D.; Akşit, K.; Steed, A.; Ritschel, T. Beyond blur:
      visualization of vector and volumetric data. Electronic           Real-time ventral metamers for foveated rendering.
      Imaging Vol. 32, No. 1, 374, 2020.                                ACM Transactions on Graphics Vol. 40, No. 4, Article
[138] Konrad, R.; Angelopoulos, A.; Wetzstein, G. Gaze-                 No. 48, 2021.
      contingent ocular parallax rendering for virtual reality.   [151] Li, D.; Du, R. F.; Babu, A.; Brumar, C. D.; Varshney,

Foveated rendering: A state-of-the-art survey                                                                          227


      A. A log-rectilinear transformation for foveated         [164] Furnas, G. W. Generalized fisheye views. ACM
      360-degree video streaming. IEEE Transactions on               SIGCHI Bulletin Vol. 17, No. 4, 16–23, 1986.
      Visualization and Computer Graphics Vol. 27, No. 5,      [165] Sarkar, M.; Brown, M. H. Graphical fisheye views of
      2638–2647, 2021.                                               graphs. In: Proceedings of the SIGCHI Conference on
[152] Shi, X. H.; Wang, L. L.; Wei, X. H.; Yan, L. Q.                Human Factors in Computing Systems, 83–91, 1992.
      Foveated photon mapping. IEEE Transactions on            [166] Lamping, J.; Rao, R.; Pirolli, P. A focus+context
      Visualization and Computer Graphics Vol. 27, No. 11,           technique based on hyperbolic geometry for visualizing
      4183–4193, 2021.                                               large hierarchies. In: Proceedings of the SIGCHI
[153] Chakravarthula, P.; Zhang, Z.; Tursun, O.;                     Conference on Human Factors in Computing Systems,
      Didyk, P.; Sun, Q.; Fuchs, H. Gaze-contingent                  401–408, 1995.
      retinal speckle suppression for perceptually-matched     [167] Carpendale, T.; Cowperthwaite, D. J.; Fracchia, F.
      foveated holographic displays. IEEE Transactions on            D. Distortion viewing techniques for 3-dimensional
      Visualization and Computer Graphics Vol. 27, No. 11,           data. In: Proceedings of the IEEE Symposium on
      4194–4203, 2021.                                               Information Visualization, 46–53, 1996.
[154] Jindal, A.; Wolski, K.; Myszkowski, K.; Mantiuk, R.      [168] Plaisant, C.; Grosjean, J.; Bederson, B. B. SpaceTree:
      K. Perceptual model for adaptive local shading and             Supporting exploration in large node link tree, design
      refresh rate. ACM Transactions on Graphics Vol. 40,            evolution and empirical evaluation. In: Proceedings
                                                                     of the IEEE Symposium on Information Visualization,
      No. 6, Article No. 281, 2021.
                                                                     57–64, 2002.
[155] Alwani, R. Microsoft and Nvidia tech to bring
                                                               [169] Kosara, R.; Miksch, S.; Hauser, H. Focus context
      photorealistic games with ray tracing. 2018. Available
                                                                     taken literally. IEEE Computer Graphics and
      at https://www.gadgets360.com/laptops/news/
                                                                     Applications Vol. 22, No. 1, 22–29, 2002.
      microsoft-dxr-nvidia-rtx-ray-tracing-volta-gpu-metro-
                                                               [170] Munzner, T.; Guimbretière, F.; Tasiran, S.; Zhang, L.;
      exodus-1826988.
                                                                     Zhou, Y. H. TreeJuxtaposer: Scalable tree comparison
[156] Sanzharov, V. V.; Frolov, V. A.; Galaktionov, V. A.
                                                                     using Focus+Context with guaranteed visibility. ACM
      Survey of nvidia RTX technology. Programming and
                                                                     Transactions on Graphics Vol. 22, No. 3, 453–462, 2003.
      Computing Software Vol. 46, No. 4, 297–304, 2020.
                                                               [171] Viola, I.; Kanitsar, A.; Groller, M. E. Importance-
[157] Mukhina, K.; Bezgodov, A. The method for real-time
                                                                     driven volume rendering. In: Proceedings of the IEEE
      cloud rendering. Procedia Computer Science Vol. 66,
                                                                     Visualization, 139–145, 2004.
      697–704, 2015.
                                                               [172] Cater, K.; Chalmers, A.; Ledda, P. Selective quality
[158] Clark, J. H. Hierarchical geometric models for visible
                                                                     rendering by exploiting human inattentional blindness:
      surface algorithms. Communications of the ACM                  Looking but not seeing. In: Proceedings of the
      Vol. 19, No. 10, 547–554, 1976.                                ACM Symposium on Virtual Reality Software and
[159] Luebke, D.; Reddy, M.; Cohen, J. D.; Varshney, A.;             Technology, 17–24, 2002.
      Watson, B.; Huebner, R. Temporal detail. In: Level       [173] Cater, K.; Chalmers, A.; Ward, G. Detail to attention:
      of Detail for 3D Graphics. Amsterdam: Elsevier, 301–           Exploiting visual tasks for selective rendering. In:
      329, xvii, 2003.                                               Proceedings of the 14th Eurographics Workshop on
[160] Hoppe, H. Progressive meshes. In: Proceedings of the           Rendering, 270–280, 2003.
      23rd Annual Conference on Computer Graphics and          [174] Sundstedt, V.; Chalmers, A.; Cater, K. Selective
      Interactive Techniques, 99–108, 1996.                          rendering of task related scenes. In: Proceedings of
[161] Rovamo, J.; Virsu, V. An estimation and application of         the Symposium on Applied Perception in Graphics
      the human cortical magnification factor. Experimental          and Visualization, 174, 2004.
      Brain Research Vol. 37, No. 3, 495–510, 1979.            [175] Sundstedt, V.; Chalmers, A.; Cater, K.; Debattista,
[162] Ramasubramanian, M.; Pattanaik, S. N.; Greenberg,              K. Top-down visual attention for efficient rendering
      D. P. A perceptually based physical error metric               of task related scenes. In: Proceedings of the Vision,
      for realistic image synthesis. In: Proceedings of the          Modeling and Visualization, 209–216, 2004.
      26th Annual Conference on Computer Graphics and          [176] Duchowski, A. T.; McCormick, B. H. Simple
      Interactive Techniques, 73–82, 1999.                           multiresolution approach for representing multiple
[163] Myszkowski, K.; Tawara, T.; Akamine, H.; Seidel,               regions of interest (ROIs). In: Proceedings of the SPIE
      H. P. Perception-guided global illumination solution           2501, Visual Communications and Image Processing,
      for animation rendering. In: Proceedings of the                175–186, 1995.
      28th Annual Conference on Computer Graphics and          [177] Geisler, W. S.; Perry, J. S. Variable-resolution
      Interactive Techniques, 221–230, 2001.                         displays for visual communication and simulation.

228                                                                                                      L. Wang, X. Shi, Y. Liu


      SID Symposium Digest of Technical Papers Vol. 30,            [191] Rimac-Drlje, S.; Vranješ, M.; Žagar, D. Foveated
      No. 1, 420–423, 1999.                                              mean squared error—A novel video quality metric.
[178] Parkhurst, D.; Culurciello, E.; Niebur, E. Evaluating              Multimedia Tools and Applications Vol. 49, No. 3,
      variable resolution displays with visual search: Task              425–445, 2010.
      performance and eye movements. In: Proceedings               [192] Tsai, W. J.; Liu, Y. S. Foveation-based image quality
      of the Symposium on Eye Tracking Research &                        assessment. In: Proceedings of the IEEE Visual
      Applications, 105–109, 2000.                                       Communications and Image Processing Conference,
[179] Geisler, W. S.; Perry, J. S. Real-time simulation                  25–28, 2014.
      of arbitrary visual fields. In: Proceedings of the
      Symposium on Eye Tracking Research & Applications,                                Lili Wang is a professor at the School
      83–87, 2002.                                                                      of Computer Science and Engineering,
[180] Willberger, T.; Musterle, C.; Bergmann, S. Deferred                               Beihang University, and a researcher of
      hybrid path tracing. In: Ray Tracing Gems. Berkeley:                              the State Key Laboratory of Virtual
      Apress, 475–492, 2019.                                                            Reality Technology and Systems. Her
[181] Jin, B.; Ihm, I.; Chang, B.; Park, C.; Lee, W.; Jung,                             research interests include virtual reality,
      S. Selective and adaptive supersampling for real-time                             augmented reality, and rendering.
      ray tracing. In: Proceedings of the Conference on
      High Performance Graphics, 117–125, 2009.
                                                                                        Xuehuai Shi is a Ph.D. student at
[182] Koskela, M.; Immonen, K.; Mäkitalo, M.; Foi, A.;                                 the School of Computer Science and
      Viitanen, T.; Jääskeläinen, P.; Kultala, H.; Takala, J.                        Engineering, Beihang University, China.
      Blockwise multi-order feature regression for real-time                            His current research focuses on virtual
      path-tracing reconstruction. ACM Transactions on                                  reality and foveated rendering.
      Graphics Vol. 38, No. 5, Article No. 138, 2019.
[183] Sherrington, C. S. On Reciprocal Action in the Retina
      as studied by means of some Rotating Discs. The
      Journal of Physiology Vol. 21, No. 1, 33–54, 1897.
                                                                                        Yi Liu is a master student at the School
[184] Arabadzhiyska, E.; Tursun, O. T.; Myszkowski,                                     of Computer Science and Engineering,
      K.; Seidel, H. P.; Didyk, P. Saccade landing                                      Beihang University, China. His current
      position prediction for gaze-contingent rendering.                                research focuses on virutal reailty,
      ACM Transactions on Graphics Vol. 36, No. 4, Article                              augumented reality, and rendering.
      No. 50, 2017.
[185] Mlot, E. G.; Bahmani, H.; Wahl, S.; Kasneci, E. 3D
      gaze estimation using eye vergence. In: Proceedings
      of the International Joint Conference on Biomedical          Open Access This article is licensed under a Creative
      Engineering Systems and Technologies, 125–131, 2016.         Commons Attribution 4.0 International License, which
[186] Veach, E. Robust Monte Carlo methods for                     permits use, sharing, adaptation, distribution and reproduc-
      light transport simulation. Ph.D. Thesis. Stanford           tion in any medium or format, as long as you give appropriate
      University, 1997.                                            credit to the original author(s) and the source, provide a link
[187] Georgiev, I.; Křivánek, J.; Davidovič, T.; Slusallek,     to the Creative Commons licence, and indicate if changes
                                                                   were made.
      P. Light transport simulation with vertex connection
      and merging. ACM Transactions on Graphics Vol. 31,              The images or other third party material in this article are
      No. 6, Article No. 192, 2012.                                included in the article’s Creative Commons licence, unless
                                                                   indicated otherwise in a credit line to the material. If material
[188] Lee, S.; Pattichis, M. S.; Bovik, A. C. Foveated video
                                                                   is not included in the article’s Creative Commons licence and
      quality assessment. IEEE Transactions on Multimedia
                                                                   your intended use is not permitted by statutory regulation or
      Vol. 4, No. 1, 129–132, 2002.
                                                                   exceeds the permitted use, you will need to obtain permission
[189] Wang, Z.; Conrad Bovik, A.; Lu, L.; Kouloheris, J. L.        directly from the copyright holder.
      Foveated wavelet image quality index. In: Proceedings           To view a copy of this licence, visit http://
      of the SPIE 4472, Applications of Digital Image              creativecommons.org/licenses/by/4.0/.
      Processing XXIV, 2001.                                       Other papers from this open access journal are available
[190] You, J. Y.; Ebrahimi, T.; Perkis, A. Attention driven        free of charge from http://www.springer.com/journal/41095.
      foveated video quality assessment. IEEE Transactions         To submit a manuscript, please go to https://www.
      on Image Processing Vol. 23, No. 1, 200–213, 2014.           editorialmanager.com/cvmj.
