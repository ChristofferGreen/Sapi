# 02-image-based-crowd-rendering

Image-Based Modeling, Rendering, and Lighting




Image-Based                                                                                               Franco Tecchia and Céline Loscos
                                                                                                          University College London


Crowd Rendering                                                                                           Yiorgos Chrysanthou
                                                                                                          University of Cyprus


                                                                                                          Approach in a nutshell
                                      P
                               opulated virtual urban environments are
                               important in many applications, from
                urban planning to entertainment. At the current stage
                                                                                                             Rendering populated urban environments requires
                                                                                                          the synthesis of two separate problems: real-time visu-
                of technology, users can interactively navigate through                                   alization of large-scale static environments and visual-
                complex, polygon-based scenes rendered with sophis-                                       ization of animated crowds and trafﬁc. Because both are
                ticated lighting effects and high-quality antialiasing                                    expensive to render, it’s essential to reduce the amount
                techniques. As a result, animated characters (or agents)                                  of time required to display each frame. We believe that
                that users can interact with are also becoming increas-                                   our effort on real-time animated crowd display, com-
                ingly common. However, rendering crowded scenes                                           bined with accelerating techniques for walk-throughs
                with thousands of different animated virtual people in                                    in virtual environments, should allow high-quality visu-
                real time is still challenging.                                                           alization of big cities.
                                          To address this, we developed an                                   Large-scale environments contain millions of poly-
                                      image-based rendering approach for                                  gons. Although we can display and visualize thousands
We propose methods for                displaying multiple avatars. We take                                of polygons at a real-time frame rate, delays appear
                                      advantage of the properties of the                                  between frames for a larger number of polygons,
rendering real-time                   urban environment and the way a                                     decreasing the visualization’s quality and the user’s abil-
                                      viewer and the avatars move within                                  ity to walk through. There has been a lot of published
animated crowds in virtual            it to produce fast rendering, based on                              work on this subject. In general, we can use three dif-
                                      positional and directional discretiza-                              ferent classes of methods to accelerate rendering of large
cities. We developed an               tion. To display many different indi-                               environments: visibility culling, imaged-based render-
                                      vidual people at interactive frame                                  ing, and level-of-detail representation. In our case, we
image-based rendering                 rates, we combined texture com-                                     need to reduce the number of polygons to display and
                                      pression with multipass rendering.                                  take care of the avatars’ real-time animation. Visibility
approach for displaying                   Our system allows real-time ren-                                culling can be an efﬁcient acceleration in urban scenes,
                                      dering of densely populated large-                                  but we would still need to render many polygons. For
multiple avatars.                     scale environments. The rendering                                   example, think about a crowded square. A user might
                                      speed is independent of the avatar                                  visualize thousands of virtual avatars and view the sur-
                model’s complexity, although rendering the same num-                                      rounding city details. Even the additional use of level-of-
                ber of humans would be impossible if using polygonal                                      detail techniques results in too many polygons to display.
                models. We improved already existing methods by                                              Considering these limitations, an image-based
                three main contributions. (See the “Related Work” side-                                   approach seemed more suitable for both the animation
                bar for more information on other approaches.) First,                                     and the rendering of the avatars. We focused on the low-
                we adapted the choice of the impostor to the object to                                    est level, when the viewer is at a certain distance from
                render, thus minimizing popping effects when chang-                                       the virtual humans and potentially has many of them in
                ing view. Second, we reduced the amount of texture                                        view. In applications where users need to have a closer
                memory, letting us load many different kinds of peo-                                      look, we can render only the close avatars with polygons.
                ple. Finally, we used a multipass algorithm, taking                                          To minimize geometrical complexity, we represent
                advantage of the alpha channel to select and color dif-                                   each human with a single adaptive impostor. (See the
                ferent regions of the body, which enabled the 10,000                                      “Model Sampling and Collision Avoidance” sidebar on
                people simulated in our experiment to all look differ-                                    p. 38 for more details.) We selected appropriate impos-
                ent. With the continuous increase of the texture mem-                                     tor images depending on the viewpoint position and the
                ory available in common machines, we predict that                                         animation frame. A previous approach1 has already pro-
                using such image-based rendering approaches will pro-                                     posed such a solution. However in that approach, the
                vide solutions to crowd visualization.                                                    required texture memory is excessive, resulting in a sim-


36                       March/April 2002                                                                                                       0272-1716/02/$17.00 © 2002 IEEE



 Authorized licensed use limited to: University College London. Downloaded on October 27, 2008 at 13:03 from IEEE Xplore. Restrictions apply.

Related Work
   The principle of image-based rendering techniques is to                                  However, several limitations exist in the technique. First,
replace parts of a scene’s polygonal content with images.                                it needs a lot of texture memory because 32 × 8 sample
We can either compute these images dynamically or a                                      images need to be stored in one texture. We can also see
priori. Maciel and Shirley1 used prerender images to replace                             popping between frames of animation due to the sampling
polygonal parts of a static environment in a walk-through                                of the view position—there are 11.25 degrees of difference
application. They do this individually for single objects or                             in the orientation of the object between each image.
hierarchically for clusters of objects. These images are used                            Because of the texture memory’s cost, the authors showed
in a load-balancing system to replace geometry, which is                                 animation only for a single type of character. We decided
sufficiently far away. A year later Schaufler and Sturzlinger2                           to use this method as a basis for his high efficiency, and we
and Shade et al.3 independently presented the concept of                                 tried to reduce memory requirements to the minimum.
dynamically generated impostors. They generate object
images at runtime and reused them for as long as the
introduced error remained below a threshold.
   We can find numerous algorithms in the literature that try
to generate better approximations. For example Chen and                                  References
Williams;4 Debevec, Taylor, and Malike;5 and McMillan and                                 1. P.W.C. Maciel and P. Shirley, “Visual Navigation of Large Envi-
Bishop6 warp the images to adapt them to different                                           ronments Using Textured Clusters,” P. Hanrahan and J. Winget,
viewpoints while Mark, McMillan, and Bishop7 and Darsa,                                      eds., ACM Computer Graphics (Symp. Interactive 3D Graphics),
Silva, and Varshney8 apply the images on triangular meshes                                   1995, pp. 95-102.
to better approximate the object’s shape. Schaufler9                                      2. G. Schaufler and W. Sturzlinger, “A Three-Dimensional Image
proposes a hardware-assisted approach to image warping,                                      Cache for Virtual Reality,” Computer Graphics Forum, vol. 15, no.
and Dally et al.10 use an algorithm that efficiently stores                                  3, Sept. 1996, pp. C227-C235.
image data starting from a number of input images.                                        3. J. Shade et al., “Hierarchical Image Caching for Accelerated Walk-
   The literature on human modeling and rendering is also                                    throughs of Complex Environments,” H. Rushmeier, ed., Proc.
extensive. However, the largest part of it concerns achieving                                Siggraph 96, Addison Wesley, Reading, Mass., 1996, pp. 75-82.
realistic approximations using complex and expensive                                      4. S.E. Chen and L. Williams, “View Interpolation for Image Syn-
geometric representations. Even with the help of level-of-                                   thesis,” J.T. Kajiya, ed., Computer Graphics (Siggraph 93 Proc.),
detail techniques, it would be almost impossible to use a                                    vol. 27, ACM Press, New York, 1993, pp. 279-288.
large number of such representations in a real-time system.                               5. P.E. Debevec, C.J. Taylor, and J. Malik, “Modeling and Rendering
An alternative, which Aubel and his colleagues11,12 recently                                 Architecture from Photographs: A Hybrid Geometry- and Image-
employed, is using impostors to render virtual humans. In                                    Based Approach,” Proc. Siggraph 96, Addison Wesley, Reading,
one work,11 they replace each human with a single                                            Mass., 1996, pp. 11-20.
impostor, while in another,12 they replace each body part                                 6. L. McMillan and G. Bishop, “Plenoptic Modeling: An Image-Based
with an impostor, overall using 16 impostors for each                                        Rendering System,” Computer Graphics, vol. 29, 1995, pp. 39-46.
human. In both methods, they compute the impostors                                        7. W.R. Mark, L. McMillan, and G. Bishop, “Post-Rendering 3D
dynamically and use them only for a few frames before                                        Warping,” M. Cohen and D. Zeltzer, eds., Proc. 1997 Symp. Inter-
discarding them.                                                                             active 3D Graphics, ACM Press, New York, 1997, pp. 7-16.
   Tecchia and Chrysanthou13 propose a less accurate but                                  8. L. Darsa, B.C. Silva, and A. Varshney, “Navigating Static Environ-
more scalable method that uses fully precomputed images.                                     ments Using Image-Space Simplification and Morphing,” M.
They show results with only one individual replicated many                                   Cohen and D. Zeltzer, eds., Proc. 1997 Symp. Interactive 3D Graph-
times due to the excessive texture requirements. Part of our                                 ics (ACM Siggraph), ACM Press, New York, 1997, pp. 25-34.
work is based on this approach, which mapped an                                           9. G. Schaufler, “Per-Object Image Warping With Layered Impos-
appropriate texture onto an impostor to display walking                                      tors,” Proc. 9th Eurographics Workshop Rendering 98, Springer
humans. To generate the impostors, Tecchia and                                               Computer Science, New York, 1998, pp. 145-156.
Chrysanthou created a set of textures, each corresponding                                10. W.J. Dally et al., The Delta Tree: An Object-Centered Approach to
to an animation frame. Each texture is composed of a set of                                  Image-Based Rendering, tech. memo AIM-1604, Massachusetts
images of the character taken from different positions. They                                 Inst. of Tech., Artificial Intelligence Laboratory, May 1996.
used a sampled hemisphere to capture the images, from 32                                 11. A. Aubel, R. Boulic, and D. Thalmann, “Animated Impostors for
positions around the character and eight elevations. At                                      Real-Time Display of Numerous Virtual Humans,” J.-C. Heudin,
runtime, depending on the view position with respect to                                      ed., Proc. 1st Int’l Conf. Virtual Worlds (VW-98), vol. 1434, Springer,
each individual, they chose the most appropriate image and                                   Berlin, 1998, pp. 14-28.
displayed it on an impostor, which is a single polygon                                   12. A. Aubel, R. Boulic, and D. Thalmann, “Lowering the Cost of Vir-
dynamically oriented toward the viewpoint. No                                                tual Human Rendering with Structured Animated Impostors,”
interpolation is used between views, as this would be too                                    Proc. 7th Int’l Conf. in Central Europe on Computer Graphics, Visu-
CPU-intensive. The appropriate texture to map depends on                                     alization, and Interactive Digital Media (WSCG 99), Univ. of West
the viewpoint and animation frame. To improve the                                            Bohemia Press, Czech Republic, Plzen, 1999.
rendering speed, they draw the humans frame by frame of                                  13. F. Tecchia and Y. Chrysanthou, “Real-Time Rendering of Densely
animation and load the textures only once per frame of                                       Populated Urban Environments,” Proc. Rendering Techniques 2000,
rendering.                                                                                   Springer Computer Science, New York, 2000, pp. 83-88.




                                                                                              IEEE Computer Graphics and Applications                             37

Authorized licensed use limited to: University College London. Downloaded on October 27, 2008 at 13:03 from IEEE Xplore. Restrictions apply.

Image-Based Modeling, Rendering, and Lighting




                                                                                                          Model Sampling and Collision
                                                                                                          Avoidance
                                                                                                             Tecchia and Chrysanthou1 initially reported the
                                                                                                          idea of using prerendered animated impostors for
A Sampling the                                                                                            real-time crowd rendering. As in that work, we
models.                                                                                                   took sample images of the detailed human model
                                                                                                          from around a discretized hemisphere, using a
                                                                                                          regular subdivision (32 views across and eight
                                                                                                          different elevations). We created and animated the
                                                                                                          original polygonal models using Curious Labs
                                                                                                          Poser (see Figure A).
                                                                                                             To develop some simple behavior simulation,
                                                                                                          we implemented fast and efficient collision
                                                                                                          detection using a regular grid.1 We call this grid a
                                                                                                          height map, with each of its cells representing
                                                                                                          about 30 × 30 cm of the environment and storing
                                                                                                          the elevation at that point. We constructed this
B A simple                                                                                                information efficiently using rasterization
collision test.                                                                                           hardware.
Particles                                                                                                    At start-up, we take an orthographic rendering
compare the                                                                                               of the static model with the camera looking down
elevation of the                                                                                          from above. Then the contents of the z-buffer are
actual and                                                                                                read making the height map (see Figure B). When
destination                                                                                               the humans move around, they access this
cells.                                                                                                    information to check the environment’s
                                                                                                          properties. We interpret high discontinuities in the
                                                                                                          elevation of adjacent cells as obstacles. Agents
                                                                                                          moving around detect such discontinuities and
                                                                                                          adjust their direction accordingly. (Tecchia et al.
                                                                                                          also reported a more general use of a 2D grid to
                                                                                                          control crowd behavior.2)


                         ulation that includes only one type of avatar. Our work                          crowds with improved quality while keeping the ren-
                         increases rendering quality using aggressive optimiza-                           dering cost low. We minimize the popping effect when
                         tions and adds important environmental effects such as                           changing views by choosing the impostor representation
                         shadows.                                                                         that best ﬁts walking humans. We can apply the tech-
                            We analyzed all the improvements needed to allow                              nique we used to select the best-ﬁtting impostor, how-
                         more variety with an increase of the visual quality, while                       ever, to other kinds of objects. We also decided on a
                         keeping a real-time frame rate. This led us to the set of                        strategy to decrease the amount of texture memory
                         new techniques we present here, which together display                           required for one human, as well as ﬁnd new displaying
                                                                                                                             methods to make every avatar look
                                                                                                                             different. To minimize the memory
                                                                                                                             consumption, we dropped the
                                                                                                                             images’ regular-grid organization,
                                                                                                                             removing all the unused space in the
                                                                                                                             impostor images set, which reduces
                                                                                                                             the memory requirements by about
                                                                                                                             three-quarters. This compression
                                                                                                                             technique reduces the size of the
                                                                                                                             required texture memory for each
1 The crowd                                                                                                                  kind of human, letting us add sever-
rendering                                                                                                                    al kinds of humans. To enhance the
system.                                                                                                                      crowd variety without increasing the
                                                                                                                             memory usage, we used multipass
                                                                                                                             rendering. Figure 1 shows an exam-
                                                                                                                             ple of the ﬁnal rendering system.

                                                                                                                                    Choosing the impostor
                                                                                                                                    representation
                                                                                                                                        When we use image-based repre-


38                       March/April 2002


 Authorized licensed use limited to: University College London. Downloaded on October 27, 2008 at 13:03 from IEEE Xplore. Restrictions apply.

sentation to render complex objects, two common forms
of artifacts may arise: missing data due to interocclusion
                                                                                        P1
can cause black regions to appear, and popping effects
can occur when we warp and/or blend the image sam-                                                                                                2 Error intro-
ples to obtain the ﬁnal image. As we already mentioned,                                                                                           duced when
we try to maximize the rendering speed using a minimal                                                                                            changing the
geometric complexity for each impostor; this leads us to                                                                                          viewpoint. This
use a single polygon as the plane on which to project a                                        P                                                  error is propor-
sample. In this scenario, the main perceived artifact is                                                                                          tional to the
the popping between different samples as the viewpoint                                                                                            distance
changes. Unfortunately, the multipass algorithm our sys-                                                                                          between the 3D
tem uses to improve the crowd variety prevents us from                                                                                            point and the
blending different samples, a solution that could have                                                                                            projection
mitigated the problem.                                                                                                                            plane.
   Another way to reduce the popping effect could be to             New                              Original
                                                                    view                              view
augment the number of samples. However, because we
still want to minimize the memory consumption, we pre-
ferred to use some other methods. Because we have only
a limited number of image samples
available, we decided to accept this
popping effect up to a certain extent,                                                                                                            3 Distance of
while attempting to minimize it.                                                                                                                  the visible
   The popping artifact occurs                                                                                                                    samples from
because all the points on the surface                                                                                                             the impostor
of the sampled object are projected                                                                                                               plane.
onto the same plane, from the direc-                                                                                                              (a) The plane is
tion that the camera is facing when                                                                                                               perpendicular
the sample is created. Obviously, as                                                                                                              to the camera
the camera position changes, the                                                                                                                  direction.
projection of such points on the                                                                                                                  (b) We chose
impostor can’t change, and the cur-                                                                                                               the best-fitting
                                         (a)                                               (b)
rent impostor is no longer an exact                                                                                                               plane to mini-
replica of the object appearance.                          View                                        View                                       mize the dis-
The amount of error for a generic                          direction                                   direction                                  tance between
                                                                          Visible points (pixels)
point on the object surface is pro-                                                                                                               sample points
portional to the distance of the point                                                                                                            and the projec-
from the projection plane. Figure 2                                                                                                               tion plane.
demonstrates this.                                          camera moves away from the sampling position. In some
   The plane researchers commonly use as the projec- extreme cases, for a particular plane orientation and a
tion plane for an impostor is usually the one perpendic- certain distance of the camera, perspective distortions
ular to the view direction from which the sample image can also become too evident (see Figure 3a). This is
was taken. This plane doesn’t take into account the more visible when moving upward rather than around
object’s shape nor any kind of special occlusion that because our object (the avatar) is longer along that
could be in the image. We then decided to try a different dimension.
approach: Given an object and the camera position from         Because we couldn’t use the best-ﬁtting plane com-
where we created the sample image, we searched for puted with PCA as is, we reduced the artifacts by com-
the projection plane passing through the object that bining the plane’s two candidate orientations. Starting
minimizes the sum of the distances of the sampled from an impostor plane purely perpendicular to the
points and the projection plane.                            camera, we “perturbed” its orientation using the result-
   To apply this idea, we had to project back in the 3D ing plane obtained from a PCA of the sample image (see
space the points visible in the impostor image to get 3D Figure 3b). This minimized the popping while limiting
visible samples of the object. We applied a Principal the introduction of other artifacts. In practice, we found
Component Analysis (PCA) to the set of 3D points and that averaging the two directions worked well.
identiﬁed the two principal eigenvectors as directions
describing the projection plane. In the case of sample Image compression
human polygonal models, such a plane results in a sig-         Although the hardware texture memory available has
niﬁcantly better approximation of the position of the vis- increased, we should still make an effort to reduce the
ible pixels with respect to the actual point positions in amount used to display virtual humans. First, because
3D. Unfortunately, other visual artifacts arose when we humans are walking, the movement is symmetric.
used the best-ﬁtting plane as the impostor plane. In fact, Instead of 32 samples, we can then reduce it to 16 and
the special orientation of this new plane asymmetrical- get the other 16 by mirroring the texture. We can see
ly warps the image depending on which direction the such symmetry in other objects, such as cars or bicycles,


                                                                                                 IEEE Computer Graphics and Applications                       39

   Authorized licensed use limited to: University College London. Downloaded on October 27, 2008 at 13:03 from IEEE Xplore. Restrictions apply.

Image-Based Modeling, Rendering, and Lighting




4 Impostor
texture for an
animation
frame using the
Tecchia and
Chrysanthou
method.1




                         and this approximation may be useful for them as well.                           the memory required for the samples, we stored each
                            Second, all the images are the same size. This results in                     animation frame using a single image of 512 × 512 pixel
                         a considerable waste of space, because for some images,                          as a total size. Figure 5 shows an example of the result-
                         the human ﬁts a restricted area. We started by placing the                       ing texture. We then stored the texture using the OpenGL
                         samples on a texture using a regular grid.1 Each sample                          compressed format (http://oss.sgi.com/projects/
                         is a prerendered ray-traced image of 256 × 256 pixels of                         ogl-sample/registry/EXT/texture compressions3tc.txt),
                         the character, using an orthographic projection. Figure                          which gives a further memory compression ratio of 1:4.
                         4 shows the resulting image. In this way, extracting a par-                      This ratio is efﬁcient, although the image loses part of its
                         ticular sample is a trivial and fast operation, but there’s a                    quality. The compression format lets us keep alpha val-
                         lot of unused texture space around each sample that gets                         ues and encodes them in 4 bits. Once loaded in texture
                         wasted. To minimize the amount of unused regions, dur-                           memory, each animation frame for a single human model
                         ing the preprocessing phase, we computed the smallest                            requires 256 Kbytes.
                         rectangle containing the character for each sample. Then,                           Because we no longer have a regular grid, we now
                         we combined all these samples in a single image, reorga-                         must precompute appropriate texture coordinates and
                         nizing them to minimize the unused space. Thanks to this                         store them for each sample. Then, at rendering time, we
                         process, the resulting new image is much smaller than                            need to compute on the ﬂy the right size and orienta-
                         the original without any loss of image quality.                                  tion for the impostor to avoid introducing distortions of
                            With our current reorganization strategy, we can                              the sample image. It’s important to notice that, because
                         reduce the amount of texture memory necessary to store                           of our optimal samples placement strategy, these para-
                         our human images to 25 percent of the original value. In                         meters generally vary for different frames of animation
                         our case, to have a good trade-off between the quality and                       even considering a ﬁxed point of view. Figure 5 shows an
                                                                                                                                example of the mapping and the
                                                                                                                                choice of the impostor.

5 Rendering                                                                                                                         Increasing the variety of
impostors using                                                                                                                     avatars
a compressed                                                                                                                           With this texture compression
texture. The                                                                                                                        we gain texture memory that we
bottom right                                                                                                                        can use to simulate more humans
shows the                                                                                                                           than Tecchia and Chrysanthou.1 To
texture after                                                                                                                       simulate 10 different types of
compression.                                                                                                                        human with 10 frames of anima-
We packed the                                                                                                                       tion each, we need about 25 Mbytes
images so they                                                                                                                      of texture memory. Although we
occupy only one                                                                                                                     improved the possibility of variety,
fourth of the                                                                                                                       10 different avatars aren’t enough
texture in                                                                                                                          to populate a city. Because we were
Figure 4.                                                                                                                           limited by the texture memory, we
                                                                                                                                    decided to modify the texture on
                                                                                                                                    the fly using multipass rendering.
                                                                                                                                    We can't change the shape and the


40                       March/April 2002


 Authorized licensed use limited to: University College London. Downloaded on October 27, 2008 at 13:03 from IEEE Xplore. Restrictions apply.

                                                                                                         6 Example avatars. On the left, an
                                                                                                         avatar rendered with ray tracing in
                                                                                                         3D Studio Max. In the middle, an
                                                                                                         avatar with alpha channels to
                                                                                                         identify parts to modify. On the
                                                                                                         right, an avatar rendered with
                                                                                                         multipasses regarding the alpha
                                                                                                         channel. Notice how these four
                                                                                                         avatars look different although they
                                                                                                         are built from the same 3D model.




kind of human, but we can assign a different color to
signiﬁcant parts of the body such as clothes, hair, and
skin color.                                                                                                                                       7 A virtual
   To identify such areas, we precomputed an alpha-                                                                                               human’s
channel image with a different alpha value for each part                                                                                          shadow is the
to modify (see Figure 6). (We did this using 3D Studio                                                                                            projection onto
Max. We had to turn off the antialiasing to avoid blurring                                                                                        the ground of
the borders of two adjacent regions.) Tuning the alpha                                                                                            its silhouette as
channel, we can deﬁne up to 256 different regions in the                                                                                          seen from a
texture without using compression, or up to 16 using the                                                                                          single light
s3tc compression (http://oss.sgi.com/projects/ogl-sam-                                                                                            source.
ple/registry/EXT/texture compressions3tc.txt) because
only 4 bits are available for the alpha channel. We per-
formed multipass rendering using the alpha channel to
select the parts to render. For each pass, we change the
impostor polygon color to the desired color, and we apply
the texture using the ﬂag GL_MODULATE and set the                              vided the tiles so that an avatar can be at different posi-
alpha threshold of the alpha test to the one associated                        tions on the same tile.
with the part of interest.                                                        If an avatar stays in the same tile in the next frame, it
   Computing a texture modulation preserves the shad-                          just continues to move in its current direction and no
ing because it’s already included in the texture. In our                       decision needs to be taken. In the case of the model we
experiments, we drew up to three passes, thus only                             used for the test, the collision detection map is binary.
changing each individual’s shirt and trousers color.                           When we encode the tile with black, it’s impassable and
More passes are possible because we can identify sev-                          the avatar needs to change direction. In addition, we
eral regions. However, the multipass rendering might                           performed intercollision detection between humans by
slow down the overall rendering rate, and there must                           checking if a destination tile is already occupied.
be a trade-off between variety and rendering time.                                Using the impostor approach, we can also compute
                                                                               and display the moving humans’ shadows.3 To project
Implementation details and results                                             the humans’ shadows on the ground, we exploit the fact
   We implemented and tested the methods we discuss                            that the shadow of a virtual human is the projection onto
here. For the simulation, we added some elements that                          the ground of its silhouette as seen from the light source
allow better quality for the results. To control the virtu-                    (see Figure 7). We can thus display the humans’ shadow
al humans’ motion, we subdivided the ﬂoor of the envi-                         on the ground using one of the images already stored in
ronment into regular-sized tiles. While the humans                             the database that we use for the impostor. In this way,
move around, they check information corresponding to                           with the cost of only one additional polygon corre-
the tile they occupy. Several types of information can be                      sponding to the projection of the impostor polygon on
stored,2 but presently, we only use this information for                       the ground, we create a shadow corresponding to the
collision detection and shadowing. We further subdi-                           human posture.


                                                                                                 IEEE Computer Graphics and Applications                        41

   Authorized licensed use limited to: University College London. Downloaded on October 27, 2008 at 13:03 from IEEE Xplore. Restrictions apply.

Image-Based Modeling, Rendering, and Lighting



                                                                                                                               the shadow stored in the cell it occu-
                                                                                                                               pies. The impostor polygon appro-
8 The crowd                                                                                                                    priately darkens to reflect the
visualization.                                                                                                                 shadow coverage.
Notice the                                                                                                                        We developed the system on an
number of                                                                                                                      800-MHz PC Pentium III with an
different peo-                                                                                                                 Nvidia GeForce GTS2 video card.
ple. Using the                                                                                                                 We populated our environment with
optimization                                                                                                                   six different avatars and performed
techniques in                                                                                                                  three passes to draw different col-
this article, we                                                                                                               ors, chosen randomly. For the
visualized thou-                                                                                                               results in Figures 8 and 9, we dis-
sands of differ-                                                                                                               played 2,000 avatars for each of four
ent humans in                                                                                                                  types of humans and 1,000 for each
real time.                                                                                                                     of the two last type, thus displaying
                                                                                                                               10,000 different humans. One of
                                                                                                                               these types is a jogger, thus having
                                                                                                                               an animation different from the oth-
                                                                                                                               ers. These humans move in a village
                                                                                                                               modeled with 41,260 polygons. The
                                                                                                                               display updates between 12 and 20
                                                                                                                               frames per second (frames/sec),
                                                                                                                               depending on the displayed polygo-
                                                                                                                               nal complexity. Although the ren-
                                                                                                                               dering is in real time, there’s no
                                                                                                                               trade-off made to decrease the qual-
                                                                                                                               ity. The rendering quality is as good
                                                                                                                               as if we hadn’t used optimization
9 A closer view                                                                                                                algorithms. Visit http://www.cs.ucl.
of the humans.                                                                                                                 ac.uk/research/vr/Projects/Crowds/
                                                                                                                               CGA/ for sample videos of this
                                                                                                                               implementation.
                                                                                                                                  To evaluate our simulation’s scal-
                                                                                                                               ability, we simulated different sized
                                                                                                                               crowds. The frame per second rate
                                                                                                                               for 0 people was 26.20; for 1,000
                                                                                                                               people, it was 24.08; for 5,000 peo-
                                                                                                                               ple, it was 18.26; and for 10,000
                                                                                                                               people, it was 13.35. We ran the sim-
                                                                                                                               ulation on an identical camera path
                                                                                                                               for each simulation.
                                                                                                             Rendering the city model itself already uses a lot of
                                                                                                          the resources because the average display is only 26
                             Time per frame (ms)




                                                                                                          frames/sec. In Figure 10, we plotted the same data but
                                                   80                                                     as time per frame versus the number of humans, and we
10 Number of                                       70                                                     can clearly see that the relation is almost linear. We
                                                   60
humans versus                                                                                             believe that an occlusion culling algorithm performed
                                                   50
the time per
                                                   40
                                                                                                          on the static model could help speed up the rendering.
frame.                                             30                                                     The frame rate then decreases as the number of poly-
                                                   20                                                     gons (those for the avatars) displayed increases. These
                                                   10                                                     timings also include the collision detection performed
                                                                                                          for each of the virtual humans simulated. A visibility test
                                                              5           10
                                                                                                          and an occlusion culling algorithm applied to both the
                                                        Number of humans (thousands)                      collision detection and the display of the humans could
                                                                                                          accelerate the frame rate.

                            We also cast the buildings’ shadows onto each virtu-                          Future work
                         al human extending the function of the regular grid                                Although we’ve already achieved good results, we
                         used for collision detection. We compute and store in a                          believe that there’s room for further improvements and
                         2D image the information about the height of a build-                            developments. In our implementation, we made a num-
                         ing’s shadow volumes. For each virtual human travers-                            ber of assumptions that we can now reexamine. For
                         ing the grid, we compare its height with the height of                           example, we assumed that the viewer will be at a cer-


42                       March/April 2002


 Authorized licensed use limited to: University College London. Downloaded on October 27, 2008 at 13:03 from IEEE Xplore. Restrictions apply.

tain distance away from the avatars. This lets us use                           2. F. Tecchia et al., “Agent Behaviour Simulator (abs): A Plat-
impostors that we created with orthographic projection                             form for Urban Behaviour Development,” Proc. Game Tech-
and limited texture dimensions. If we let users get clos-                          nology (GTEC 2001), CD-ROM, 2001.
er, they will notice the artifacts. One way around this is                      3. C. Loscos, F. Tecchia, and Y. Chrysanthou, “Real-Time
to use a hybrid approach where polygonal human mod-                                Shadows for Animated Crowds in Virtual Cities,” Proc. ACM
els are used instead of impostors for the few avatars that                         Symp. Virtual Reality Software and Technology, ACM Press,
come right up to the viewpoint.                                                    New York, 2002, pp. 85-92.
   Because we used the same textures to generate the                            4. F. Tecchia, C. Loscos, and Y. Chrysanthou, “Real Time Ren-
avatar shadows, we also assumed that the light source at                           dering of Populated Urban Environments,” ACM Siggraph
inﬁnite. This wasn’t a limitation for our examples because                         Technical Sketch, ACM Press, New York, Aug. 2001.
the only light source was the sun. However, if we want to
simulate the city at night with street lights, then we will
have to warp the textures before applying them.
   The impostors are currently shaded when we render                                               Franco Tecchia is a research fel-
them in 3D Studio Max. This effectively ﬁxes the shad-                                             low at the University College London,
ing to the particular light deﬁned at that time, making                                            working on real-time rendering of
the sources static. However, we believe that we could                                              populated complex environments.
shade the impostors on the ﬂy using normal maps indi-                                              His research interests include real-
cating each pixel’s orientation. This would let the shad-                                          time computer graphics, virtual and
ing be consistent if we modiﬁed the light source.                                                  augmented reality, and software
   An interesting extension to our system, that could                          engineering. He received his DrEng degree in computer
greatly improve its impact, would be using real photo-                         engineering from the University of Pisa.
graphic images of humans instead of synthetic models.
Of course, the problem here would be acquiring all the
sample images. Possibly, we could scan a person in color
and then take the samples from the scan.                                                            Céline Loscos is a lecturer at the
   Methods to cull polygons could speed up rendering                                                University College of London. Her
times, selecting for display both polygons from the sta-                                            research interests include inverse illu-
tic environments and the moving people.4                                                            mination and realistic illumination
   We could certainly use the current algorithms to ren-                                            for complex environments. She par-
der different kinds of objects such as cars, pets, children,                                        ticipates in European Union and
or groups of people (such as children holding an adult’s                                            other funded projects for real-time
hands). Also, several animations could be possible, with                       rendering for mixed interfaces, such as real-world data or
an appropriate texture load. Particular care should be                         haptics. She received an MSc and a PhD in computer sci-
taken for transitions in between animations. Moreover,                         ence from the Université Joseph Fourier in Grenoble,
using the multipass rendering algorithm, we could sim-                         France. She is an ACM and Eurographics member.
ulate simple animation such as turning a head to the left
or right.
   Finally, for each new type of object, we should do more
work on developing appropriate behavior. Although                                                  Yiorgos Chrysanthou is an
researchers have done a lot of work on behavior in cities,                                         assistant professor at the University
there are still many problems to solve, especially for real-                                       of Cyprus. His research interests are
time simulation of thousands of agents.                   ■                                        in computer graphics, virtual reali-
                                                                                                   ty, and computational geometry. He
Acknowledgments                                                                                    received a BSc in computer science
  This work was in part supported by the UK Engineer-                                              and statistics and a PhD in comput-
ing and Physical Sciences Research Council (EPSRC)                             er graphics from Queen Mary and Westﬁeld College. He is
project GR/R01576/01 and the EPSRC Interdisciplinary                           an IEEE, ACM, and Eurographics member. He also coau-
Research Centre Equator, an interdisciplinary research                         thored the book Computer Graphics and Virtual Envi-
project at University College London. (See http://www.                         ronments: From Realism to Real Time (Addison Wesley,
cs.ucl.ac.uk/research/equator/ for more information.)                          2001).

                                                                                 Readers may contact Franco Tecchia at the Dept. of Com-
                                                                               puter Science, Univ. College London, Gower St., WC1E 6BT,
References                                                                     London, UK, email f.tecchia@cs.ucl.ac.uk.
 1. F. Tecchia and Y. Chrysanthou, “Real-Time Rendering of
    Densely Populated Urban Environments,” Proc. Rendering                     For further information on this or any other computing
    Techniques 2000, Springer Computer Science, New York,                      topic, please visit our Digital Library at http://computer.
    2000, pp. 83-88.                                                           org/publications/dlib.




                                                                                                 IEEE Computer Graphics and Applications          43

   Authorized licensed use limited to: University College London. Downloaded on October 27, 2008 at 13:03 from IEEE Xplore. Restrictions apply.
