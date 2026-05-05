# 03-skeleton-based-edge-bundling-for-graph-visualization

Skeleton-based edge bundling for graph visualization
         Ozan Ersoy, Christophe Hurter, Fernando V Paulovich, Gabriel Cantareira,
                                               Alexandru C Telea



      To cite this version:
     Ozan Ersoy, Christophe Hurter, Fernando V Paulovich, Gabriel Cantareira, Alexandru C Telea. Skeleton-based
     edge bundling for graph visualization. IEEE Transactions on Visualization and Computer Graphics, 2011, 17
     (12), pp 2364-2373. ⟨10.1109/TVCG.2011.233⟩. ⟨hal-01021607⟩




                                        HAL Id: hal-01021607
                          https://enac.hal.science/hal-01021607v1
                                            Submitted on 21 Jul 2014




    HAL is a multi-disciplinary open access archive             L’archive ouverte pluridisciplinaire HAL, est des-
for the deposit and dissemination of scientific re-        tinée au dépôt et à la diffusion de documents scien-
search documents, whether they are published or not.       tifiques de niveau recherche, publiés ou non, émanant
The documents may come from teaching and research          des établissements d’enseignement et de recherche
institutions in France or abroad, or from public or pri-   français ou étrangers, des laboratoires publics ou
vate research centers.                                     privés.


                                              HAL Authorization

                Skeleton-based edge bundling for graph visualization
                                       O. Ersoy, C. Hurter, F. Paulovich, G. Cantareira, A. Telea

       Abstract— In this paper, we present a novel approach for constructing bundled layouts of general graphs. As layout cues for
       bundles, we use medial axes, or skeletons, of edges which are similar in terms of position information. We combine edge clustering,
       distance fields, and 2D skeletonization to construct progressively bundled layouts for general graphs by iteratively attracting edges
       towards the centerlines of level sets of their distance fields. Apart from clustering, our entire pipeline is image-based with an efficient
       implementation in graphics hardware. Besides speed and implementation simplicity, our method allows explicit control of the emphasis
       on structure of the bundled layout, i.e. the creation of strongly branching (organic-like) or smooth bundles. We demonstrate our method
       on several large real-world graphs.
       Index Terms—Graph layouts, edge bundles, image-based information visualization




   Graphs are among the most important data structures in informa-            local hierarchy of traffic connections in a road or airline network, or
tion visualization, and are present in many application domains in-           identifying the number and size of branches in a software structure.
cluding software comprehension, geovisualization, analysis of traf-              The structure of this paper is as follows. In Section 1, we review
fic networks, and social network exploration. Classical visualization         related work on edge bundles. Section 2 presents our bundling algo-
metaphors for general graphs include node-link diagrams [16], matrix          rithm. Section 3 details implementation. Section 4 presents appli-
plots [33], and graph splatting [34]. For specific types of graphs, such      cations on large real-world graphs. Section 5 discusses our method.
as hierarchies (trees), additional methods exist such as treemaps.            Section 6 concludes the paper and outlines future work directions.
   As the number of nodes and edges of a graph increases, node-link
graph visualizations become challenged by clutter, i.e. unorganized           1   R ELATED WORK
groups of nodes and edges onto small screen areas. To reduce clut-            Related work in reducing clutter in large graph visualizations can be
ter, and also address use-cases which focus on simplified depiction           organized as follows.
of large graphs with an emphasis on graph structure, several methods             Graph simplification techniques reduce clutter by simplifying the
have emerged. Specifically, bundling methods are an interesting al-           graph prior to layout e.g. by grouping strongly connected nodes and
ternative for classical node-link metaphors. Bundling typically starts        edges into so-called metanodes, followed by using classical node-
with a given set of node positions, either present in the input data,         link layouts for visualization. Several simplification methods exist,
or computed using a layout algorithm. Edges found to be close in              e.g. [1, 2]. Graph simplification is attractive as it reuses existing node-
terms of graph structure, geometric position of their endpoints, data at-     link layouts out of the box, but can be sensitive to simplification pa-
tributes, or combinations thereof, are drawn as tightly bundled curves.       rameters, which further depend on the type of graph being processed.
This trades clutter for overdraw, and produces images which are easier        It does not allow a continuous treatment of the graph: the simplifica-
to understand and/or better emphasize the graph structure. Edge bun-          tion events yield a set of discrete graphs rather than a smooth explo-
dles can be rendered using various effects such as blending or shad-          ration scale [21]. Also, simplification typically changes node positions
ing [14, 21, 31]. Edge bundling algorithms exist for both compound            (collapse to metanodes), which can be undesirable e.g. when positions
(hierarchy-and-association) [13] and general graphs [14, 7, 23, 21].          encode information.
   In this paper, we present a novel approach for constructing edge              Edge bundling techniques trade clutter for overdraw, by routing ge-
bundles for general graphs. We adapt a recent result which computes           ometrically and semantically related edges along similar paths. Fur-
centerlines, or skeletons, of groups of edges [31] and use the skele-         ther details on clutter causes and reduction strategies in information
ton for actual edge bundling rather than shading only. In detail, we          visualization is given in [10]. Bundling can be seen as condensing
combine edge clustering, distance fields, and 2D skeletonization to           the edges’ angle distribution along a reduced set of directions and also
construct bundled layouts by iteratively attracting edges towards the         sharpening the local edge spatial density, by making it high at bun-
centerlines of level sets of their distance fields. Apart from clustering,    dle locations and low elsewhere. This improves readability in terms
our pipeline works image-based, which allows an efficient implemen-           of finding groups of nodes related to each other by groups of edges
tation in graphics hardware. Besides speed, our method allows users to        (the bundles). Bundling increases the amount of white space between
explicitly control the emphasis on bundle structure, i.e. create strongly     bundles, which makes their visual separation easier.
branching, organic-like, or smooth, bundles, and guarantees that bun-            Dickerson et al. merge edges by reducing non-planar graphs to
dles always have a tree structure. This type of control can be helpful        planar ones [9]. Holten pioneered edge bundling under this name for
in applications where one is interested to see how several edges ’join’       compound (hierarchy-and-association) graphs by routing edges along
together into, or split from, main structures, for example when explor-       the hierarchy layout using B-splines [13]. Gansner and Koren bundle
ing the structure of a network. Examples hereof are examining the             edges in a circular node layout similar to [13] using area optimiza-
                                                                              tion metrics [12]. Dwyer et al. use curved edges in force-directed
                                                                              layouts to minimize crossings, which implicitly creates bundle-like
• O. Ersoy and A. Telea are with the University of Groningen, the             shapes. Force-directed edge bundling (FDEB) creates bundles by at-
  Netherlands, E.mail: o.ersoy@rug.nl, a.c.telea@rug.nl.                      tracting control points on edges close to each other [14]. FDEB can
• C. Hurter is with DGAC-DSNA, France, E.mail:                                be significantly optimized using multilevel clustering techniques such
  christophe-hurter@aviation-civile.gouv.fr.                                  as the MINGLE method [11]. Flow maps produce a binary clustering
• F. Paulovich and G. Cantareira are with the University of Sao Paulo,        of nodes in a directed graph representing flows to route curved edges
  Brazil, E-mail: paulovic@icmc.usp.br, cantareira@icmc.usp.br.               along [23]. Control meshes are used by several authors to route curved
 Manuscript received 31 March 2011; accepted 1 August 2011; posted online     edges, e.g. [25, 35]; a Delaunay-based extension called geometric-
23 October 2011; mailed on 14 October 2011.                                   based edge bundling (GBEB) [7]; and ’winding roads’ (WR) which
For information on obtaining reprints of this article, please send            use boundaries of Voronoi diagrams for 2D [21] and 3D [20] layouts.
email to: tvcg@computer.org.                                                     Several techniques exist for rendering bundled layouts, e.g. color
                                                                              interpolation along edges for edge directions [13, 7]; transparency or

hue for local edge density, i.e. the importance of a bundle, or for         2.2 Shape construction
edge lengths [21]. Whole bundles can be drawn as compact shapes             Clustering delivers sets of spatially close edges, i.e., the bundling
whose structure is emphasized by shaded cushions [31]. Graph splat-         candidates. Given such a cluster C = {ei }, we consider its draw-
ting visualizes node-link diagrams as continuous scalar fields using        ing ∆(C) ⊂ R2 , e.g. the set of polylines corresponding to its edges
color and/or height maps [34, 15].                                          ei if we use the default linear edge interpolation. We construct a
2 A LGORITHM                                                                compact 2D shape Ω ⊂ R2 surrounding ∆(C), as follows (see also
                                                                            Fig. 2). Given any shape Φ ⊂ R2 , we first define its distance transform
The inspiration behind our method relates to a well-known fact in
                                                                            DTΦ : R2 → R+ as
shape analysis: given a 2D shape, its skeleton is a curve locally cen-
tered with respect to the shape’s boundary [6]. Skeleton branches cap-
                                                                                                 DTΦ (x ∈ R2 ) = min kx − yk                      (2)
ture well the topology of elongated shapes [19, 28]. Hence, if we could                                            y∈Φ
create such shapes from sets of edges in a graph, their skeletons could
be suitable locations for bundling. To this end, we propose a skeleton-
based edge bundling method, as follows (see Fig. 1):
  1. we cluster edges into groups Ci which have strong geometrical
     and optionally attribute-based similarity;
  2. for each cluster C, we compute a thin shape Ω surrounding its
     edges using a distance-based method;
  3. for each shape Ω, we compute its skeleton SΩ and feature trans-
     form of the skeleton FTS ;
  4. for each cluster C, we attract its edges towards SΩ using FTS ;
                                                                                                             a)                            b)
  5. we repeat the process from step 1 or step 2 until the desired
     bundling level is reached;
  6. we perform a final smoothing and next render the graph using a
     cushion-like technique to help understanding bundle overlaps.
    We start with an unbundled graph G = (V, E) with nodes V and
edges E. We assume that we have node positions vi ∈ R2 , either from
input data, or from laying out G with any existing method e.g. spring
embedders [16]. Edges ei ∈ E are sampled as a set of points connected
by linear interpolation; other schemes such as splines work equally
well. The start and end points of an edge, denoted esi and eei respec-
tively, are the positions of the nodes the edge connects. Edge points                                        c)                             d)
may come from input data, e.g. when we bundle a graph which has
                                                                            Fig. 2. Shape construction: a) ∂ Ω and S; b) DTS ; c) FTS ; d) bundling
explicit edge geometry. If no edge positions are available, we initial-     result (see Secs. 2.2-2.4 for details)
ize the edge points by uniformly sampling the line segments (esi , eei )
with some small step. Our bundling algorithm iteratively updates these        Given a distance value ω , we next define our shape Ω as
edge points. Its output is a bundled layout of G which keeps node po-
sitions intact and adjusts the edge points to represent bundled edges.                          Ω = {x ∈ R2 |DT∆(C) (x) ≤ ω }                     (3)
    The six steps of our method are explained next.
                                                                            where DT∆(C) is the distance transform of the drawing ∆(C) of C’s
2.1 Clustering
                                                                            edges. The shape’s boundary ∂ Ω is the level set of value ω of DT∆(C)
To obtain elongated 2D shapes, needed for our bundling (described
                                                                            (see Fig. 2 a). This is equivalent to inflating ∆(C) with a distance ω in
next in Sec. 2.3), we first cluster edges using a similarity metric
                                                                            all directions. In practice, we set ω to a small fraction (e.g. 0.05) of
which groups same-direction, spatially close, edges, using the clus-
                                                                            the bounding box of G. Efficient computation of distance transforms
tering method described in [31]. We have tested several clustering al-
                                                                            is detailed further in Sec. 3.
gorithms: hierarchical bottom-up agglomerative (HBA) clustering us-
ing full, centroid, single, and average linkage, and k-means clustering,    2.3 Shape creation
both with Euclidean and statistical correlation (Pearson, Spearmans
                                                                            Given a shape Ω computed from an edge cluster drawing as outlined
rank, Kendalls τ ) distances. HBA with full linkage and Euclidean dis-
tance given by                                                              above, we next compute its skeleton SΩ defined as
                                  v
                                                                             SΩ = {x ∈ Ω|∃y, z ∈ ∂ Ω, y 6= z, kx − zk = ky − zk = DT∂ Ω (x)} (4)
                                  uN
                                    ∑
                                  u
                      d(e , e ) = t ke − e k2
                        i   j            ik    jk                    (1)
                                   k=1                                      i.e. the set of points in Ω which admit at least two different so-called
                                                                            feature points on ∂ Ω, at distance equal to the distance transform of ∂ Ω
where ei j, j∈1,N are uniformly spaced sample points along the edges,
                                                                            (Fig. 2 a).
with N ∈ [50, 100], gives the best results, i.e. clusters with geomet-          Given S, we now compute its so-called one-point feature transform
rically close edges which naturally follow the graph structure. Using       FTS : R2 → R2 , defined as
the same N for all edges removes edge length bias. HBA delivers a
dendrogram D = {Ci } with the edge set E as leaves and similarity                            FTS (x) = {y ∈ S|DTS (x) = kx − yk}                  (5)
(linkage) values d(C), equal to the full linkage of cluster C based on
the distance metric in Eqn. 1, increasing from root to leaves. We select    i.e. one of the feature points of x. Figure 2 b,c show the DTS and FTS of
a ’cut’ in D, or partition, P = {Ci ∈ D|d(Ci ) < δ } of E based on a sim-   a skeleton. Gray values in Fig. 2 b indicate the DTS value (low=black,
ilarity value δ , set by our algorithm as explained further in Secs. 2.5    high=white). Colors in Fig. 2 c indicate the identity of different feature
and 3. If desired, d in Eqn. 1 can be easily adapted to incorporate edge    points - same-color regions correspond roughly to the Voronoi regions
data attributes, as outlined in [31].                                       of the skeleton branches [32]. The skeleton is the identity set of FTS ,

                                                                   I iterations

               δ                 ω         Shape construction                                     Edge bundling         α,β              Postprocessing
                           distance                                feature                         path                            relaxation &
       clustering                            skeletonization                      tip detection                    attraction                      rendering
                           transform                               transform                       computation                     smoothing
                                                     ρ                                                                                    γs,γr

   input     cluster set           shapes Ω              skeletons SΩ    image data       skeleton tips   skeleton paths bundled edges   smooth bundles     final
   graph                                                                                                                           end user                 image

Fig. 1. Skeleton-based edge bundling pipeline. End user parameters are marked in green. System preset parameters are in red

i.e. ∀x ∈ S, FTS (x) = x. Note that, in Eqn. 5, we use the distance                       smoothly edges twist, or curve, from their nodes to reach their bundled
transform DTS of the skeleton S, and not the distance transform DT∂ Ω                     location. Higher K values produce more twists, and low K values
of the shape. Also, note that the one-point feature transform is simpler                  produce smoother twists. Values of K ∈ [3, 6] give very similar results
than the so-called full feature transform                                                 to known bundling methods e.g. [13, 14, 21]. Also, for any x ∈ S,
                               f ull
                                                                                          FTS (x) = x (Sec. 2.3), so for such points we have xnew = x (Eqn. 7), i.e.
                           FTS         (x) = argmin kx − yk                       (6)     points which have reached the skeleton, the extreme bundling location,
                                              y∈S                                         do not move any longer.
                                                                                             Equation 7 is equivalent to advecting edge points x in the gradi-
which records all feature points of x [6].
                                                                                          ent field −∇DTS . Distance transforms of any shape except a straight
   In practice, we compute distance transforms, one-point feature
                                                                                          line have div ∇DTS 6= 0 [27]. Hence, our attraction typically shortens
transforms, and skeletons in discrete image (screen) space. This al-
                                                                                          and/or lengthens edges, since these get immediately curved after one
lows efficient implementation (see Sec. 3) and also further processing
                                                                                          application of Eqn. 7. We compute the edge points x used in Eqn. 7
of the skeleton for edge bundling, as described next.
                                                                                          by uniformly sampling edges in arc-length space with a distance equal
2.4 Edge attraction                                                                       to a small fixed fraction (0.05) of the layout’s bounding box. This
                                                                                          removes points where the edge contracts (div ∇DTS < 0) and inserts
Using the skeleton S and its feature transform FTS , we now bundle the
                                                                                          points where the edge dilates (div ∇DTS > 0) as needed, thus ensuring
edges ei ∈ C by attracting a discrete representation of each edge to-
                                                                                          a uniform edge sampling density.
wards S. This idea is based on the following observations. First, given
the way we combine clustering and edge bundling, a cluster contains
only edges having close trajectories; the reasons for this are detailed                   2.4.1 Attraction singularities
in Sec. 2.5. By construction, the skeleton S of a cluster is locally cen-                 As explained, Eqn. 7 is equivalent to advecting x in the field −∇DTS .
tered with respect to the (similar) edges in that cluster, i.e. a good                    This field is smooth everywhere in R2 except on points x where
candidate for the position to bundle towards. Secondly, FTS (x) − x                             f ull
                                                                                          kFTS (x)k > 1, i.e. points located on the skeleton of the skeleton’s
gives, for each point x ∈ R2 , the direction vector from x to the closest
                                                                                          complement, or Voronoi diagram of S, S = SR2 \S . Intuitively, S corre-
skeleton point to x, i.e. the direction to bundle towards. We use these
observations to bundle ei as follows.                                                     sponds in Fig. 2 to color discontinuities. Although this singularity set
    First, we compute all branch termination points, or tips, T = {ti }                   is small, i.e. a set of curves in 2D, we need special treatment for such
of S. Given that S is represented in image space, we use a simple and                     situations. If we were to directly advect a curve using Eqn. 7 with no
efficient 3 × 3 pixel template-based method [18] to locate ti . Next,                     further precaution, singularities would appear where the curve crosses
we compute all skeleton paths Π = {πi ⊂ S} between any two tips                           S, since ∇DTS has a high absolute divergence, i.e. changes direction
ti and t j . The paths are represented as pixel chains and are found                      rapidly, in such areas [27]. Such singularities appear as sharp kinks in
using depth-first search from each ti on the skeleton pixel-adjacency-                    the curve, which defeats our purpose of creating smooth bundles. For
graph. We next use these paths to robustly attract the edges towards                      example, attracting the blue edge e in Fig. 3 a towards the Y-shaped
the skeleton.                                                                             skeleton yields the red line which shows two kinks, where e crosses S
    For each ei ∈ C with start and end points esi and eei respectively, we                (dotted line) at points a and b. The problem is made only more com-
select a skeleton path π (ei ) ∈ Π so that {FTS (esi ), FTS (eei )} ⊂ π (ei ),            plex by the fact that we use a sampled edge representation, so x may
i.e. a path passing through the feature points of both edge end points.                   be close, but not on, S.
If there are several such paths in Π, we pick any one of them, the                            We solve such situations by an implicit regularization of the ad-
particular choice having no influence on the algorithm.                                   vection field determined by FTS . First, we enforce the constraint that
    We now use π (ei ) to bundle ei along the skeleton, as follows. Con-                  points x ∈ e can only be advected to points on the edge’s path π (e).
sider a point x ∈ ei located at arc-length distance λ (x) from esi . We                   This ensures that, during advection, parts of e cannot be attracted to-
move x towards FTS (x) with a distance which is large if x is far away                    wards other skeleton branches than the set of contiguous branches
from FTS (x) and/or close to the middle of the edge:                                      which form π . Intuitively, Eqn. 7 should not pull e towards non-
                                                                                          connected skeleton branches. We achieve this constraint as follows
                          
                             λ (x)
                                              
                                                  λ (x)
                                                                                         (see Fig. 3 b). For each x ∈ e, we evaluate its FTS (x). If FTS (x) ∈ π (e),
          xnew = 1 − αφ                  x + αφ              FTS (x)     (7)              we attract the ’regular’ point x using Eqn. 7, else we mark x as special
                             λ (eei )             λ (eei )
                                                                                          case. Special points along e (yellow in Fig. 3 b) form compact sets
Here, α ∈ [0, 1] controls the tightness of bundling: Large values bring                   σi , which are preceded and followed on e by regular points σistart and
the edge closer to the skeleton, whereas small values bundle less. The                    σiend respectively, whose feature points belong to π (e) by construc-
function φ : [0, 1] → [0, 1] defined as                                                   tion. We next map each special point x to a corresponding point xmap
                                                                                          on π (e) using arc-length interpolation along both σi and their corre-
                             φ (t) = [2 min(t, 1 − t)]K                           (8)     sponding path fragments [FTS (σistart ), FTS (σiend )] ⊂ S (dark green in
                                                                                          Fig. 3 b), and use xmap in Eqn. 7 instead of FTS (x). This ensures that
modulates the motion amount so that the edge’s end points esi and eei                     both special and regular points are attracted to the same path π (e), and
do not move at all, points close to these end points move less, and                       thus, since π (e) is a compact curve, that the motion of e is smooth.
points around the middle of the edge move most. This produces the                             However, the above regularization does not eliminate all sharp
curved edge profile we require for bundling, and also keeps edge end                      kinks in the advection of an edge: Consecutive points of the edge can
points fixed to their node locations. The parameter K controls how                        ’see’ points on the same skeleton path π , and still be separated by a sin-

                                                  _
                                         skeleton S                                                    number of iterations I is reached. More iterations yield tighter bun-
                                                                   undesired result                    dled edges. This process is strictly monotonic, i.e. edges can only get
                   FTS(ei0)
                                                                                skeleton S             closer to their clusters’ skeletons (hence to each other) by construction,
                     ei0                                                                               as explained below (see also Fig. 4).
                                                                     FTS(eiN)
                                                                                                          First, let us explain why clustering needs to be repeated during the
       a)                                     a                                                        iterative process. For the first clustering, we use a high similarity
                                                                        eiN
                                                       b                                               threshold δ in order to guarantee elongated, thin, clusters regardless
                                                                                     regularization
                                                             curve to bundle                           of the edge spatial distribution in the input graph (Sec. 2.1). This
                                                  _
                                         skeleton S
                                                                                                       is essential for getting the initial bundling under way. Indeed, if we
      path fragment [FTS(σstart),FTS(σend)]                         desired result
                                                                                                       had weakly coherent clusters, these would contain edges that inter-
                    FTS(ei0)                                                                           sect each other at large angles, hence the shapes surrounding them,
                                                                                skeleton S
                                                                                                       and their skeletons, would be meaningless as bundling cues. For sub-
                     ei0
                                                                     FTS(eiN)
                                                                                                       sequent iterations, we decrease δ and recluster the graph each few
                                                      xmap                                             (3to5) iterations. This produces fewer, increasingly larger, clusters,
       b)                                σstart
                                                      x σend
                                                                         eiN                           which allows fine-scale bundles to group into coarse-scale ones. How-
                                                                                                       ever, these large clusters are locally elongated, since they contain al-
                                                             curve to bundle                           ready partially bundled edges. Hence, coarsening the clustering will
                                       special points σ                                                not group unrelated edges. The overall effect is bottom-up bundling:
                                                  _
                                         skeleton S
                                                                   undesired result
                                                                                                       First, the closest edges get bundled, yielding fine-scale local bundles,
                    FTS(ei0)                                                                           followed by increasingly coarser-scale bundle merging.
                                                                                skeleton S
                                                                                                          Similarly, we decrease α during the iterative process. Initial large
                     ei0                                                                               α values yield strongly coherent initial bundles, needed for cluster-
       c)                                         β                                                    ing stability as explained above. Subsequent relaxed α values allow
                                              a
                                                                                                       edges in more complex, larger, bundles to adjust themselves. Concrete
                           eiN
                                                                                      regularization   values for δ and α are given in Sec. 3.2.
                                                               curve to bundle
                           FTS(eiN)                _
                                          skeleton S
                                                                                                       2.6 Postprocessing
                                                                    desired result
                    FTS(ei0)
                                                                                                       2.6.1 Relaxation and smoothing
                                                                                skeleton S
                                                                                                       The output of our bundling algorithm has a strong branch-like structure
                      ei0                                                                              (see e.g. Fig. 5 f). This is the inherent effect of using skeletons as
       d)
                                                                                                       bundling cues. Indeed, skeleton branches asymptotically meet at large
                                              a
                                                                                                       angles [24]. This visual signature of our bundles may be desirable for
                            eiN
                                                                                                       use-cases where one is interested to see the branching structure of a
                                                               curve to bundle                         graph. However, often the fact that two bundles join at some point
                            FTS(eiN)
                                                                                                       in a thicker bundle is irrelevant, and should not be over-emphasized.
                                                                                                       We offer this possibility by performing a final postprocessing on the
Fig. 3. Attraction singularities. Naive solution (a,c) and corresponding                               bundled layout. Here, two variations are proposed. First, we apply
solutions with regularization (b,d). Final bundled curve is shown in red.                              a simple Laplacian smoothing filter along the edges γs times, much
Voronoi regions of the branches of S are shown in different hues
                                                                                                       like [14]. This removes sharp bundle turns, which by construction
                                                                                                       appear precisely, and only, where skeleton branches meet. Indeed, as
gularity (see point a in Fig. 3 c). As explained, advecting such points                                known from medial axis theory, a skeleton branch is always a smooth
a using Eqn. 7 would produce undesirable bends. Since the feature-                                     curve; the only curvature discontinuities along a skeleton appear at
point of a is located on the same path π (e) as those of a’s neighbors on                              branch junctions [24]. A second postprocessing we found useful is to
the edge, we cannot find a using the path-based detection criterion out-                               interpolate linearly with a value γr ∈ [0, 1] between the bundled graph
lined above. We solve this problem by using an angle-based criterion:                                  and its initial layout. This relaxes the bundling, which is desirable
Given our discrete edge representation e = {xi }, we test if the feature                               when users want to see the individual edges within a bundle and/or
vectors FTS (xi ) − xi and FTS (xi+1 ) − xi+1 of consecutive edge sample                               where these come from in the initial layout. The effect is similar to the
points xi and xi+1 form a large angle β . If β exceeds a user-defined                                  spline tightness parameter in [13].
value βmax , we mark xi as a special point and treat it as explained ear-                                 Figure 5 a,b show the effect of smoothing on a graph whose nodes
lier for the path-based detection criterion. In practice, βmax = π /4 has                              use a radial layout. Smoothing (b) removes the strong branching ef-
given good results for all graphs we tested. The overall effect is that                                fect visible in (a) at the locations indicated by arrows. The result is
sharp edge angles are eliminated and edges are advected smoothly to-                                   very similar to the HEB layout [13]. However, it is important to stress
wards the skeleton (Fig. 3 d). As a more complex example of our                                        that we obtain our bundling with no graph hierarchy information. Fig-
regularization, Fig. 2 d shows the bundling of a set of edges (green)                                  ures 5 e,f show the effect of smoothing and relaxation on the well-
close to the skeleton in Fig. 2 a.                                                                     known US airlines graph, whose bundled layout is shown in Fig. 7 j.
   Our angle criterion is a one-dimensional version of the divergence-                                 Smoothing removes the ’skeleton effect’ from the bundles, while re-
based Hamilton-Jacobi skeleton detector of [27]. It subsumes the path-                                 laxation makes these thicker with less effect on their curvature. As
based criterion. In theory, it would be sufficient to use the angle cri-                               such, the two effects serve complementary goals.
terion to achieve smooth motion. However, the path-based criterion is
more numerically robust as it involves no angle estimation or thresh-                                  2.6.2 Rendering
olding. Since its application is equally fast (we need paths anyway to                                 Finally, we propose a simple but effective rendering technique for eas-
regularize the attraction in both cases), we use it when applicable to                                 ier visual following of the rendered bundles (Fig. 5 c,d). The principle
reduce any chance for numerical instabilities.                                                         follows [31]: We render each bundle in back-to-front order, decreas-
                                                                                                       ingly sorted by skeleton pixel count |S|, as if they were covered by a
2.5 Iterative algorithm                                                                                3D cushion profile bright at the bundle’s center and dark at its periph-
For a given graph layout, one application of the clustering, shape con-                                ery. This helps following a given bundle, especially in regions where
struction, and edge attraction steps outlined above yields a new layout                                several bundles cross. In contrast to [31], we use a much simpler tech-
whose edges are closer to their respective cluster skeletons. To achieve                               nique (see Fig. 6). Edges are rendered as alpha-blended polylines. We
full bundling, we repeat this process iteratively until a user-specified                               modulate the saturation S and brightness B of each polyline point x

 iteration 1                                                                iteration 2




 iteration 4                                                                iteration 7




 iteration 10                                                               iteration 12




Fig. 4. Iterative bundling of the US migrations graph. Colors indicate edge clusters (see Sec. 2.5)

                                                                                                                                                δΒ
based on its distance to the skeleton d(x) = DTS (x), which is already              B                       S                              δS
                                                                                                                                halo
computed for the attraction phase (Sec. 2.3). For this, we use
                                                                                1                       1
                                       1 − d/δS
                                    p
                        S(d) =                                      (9)
                                        √
                        B(d) = 1 − d/δB                            (10)
                                                                                                                                              skeleton S
This yields thin, specular-like, white highlights in the middle of the                                                           bundle local width
bundles (where the skeleton is located) and darkens the edges as they                      δΒ     DTS       δS < δ Β     DTS
get further from the skeleton. The parameter δB is the local thick-
ness of the bundle. For an edge point x ∈ Ω, δB (x) = DTS (FT∂ Ω (x)),      Fig. 6. Cushion shading for bundles (Sec. 2.6.2)
i.e. the distance of the closest point on the shape boundary ∂ Ω to the
shape’s skeleton. This does not require any extra computations, since
we anyway compute FT∂ Ω and DTS as part of the shape construction           plicit representation of edge clusters allows us to easily brush or select
(Sec. 2.2, see also Sec. 3 for implementation details). The parameter       groups of edges showing up as bundles or branches thereof. Three
δS < δB controls the highlight thickness and is set to a small fraction     types of selection were found useful, as follows (see also Fig. 8 e-g
(e.g. 0.2) of δB . This technique has several differences as compared to    and example discussed in Sec. 4). Given the mouse position x, we first
splatting-based shading techniques for bundles [31, 21]. First, our ren-    select all bundled edges within a disc of small radius r centered at x
dering does not change the screen-space thickness of a bundle, which        by computing the feature transform of the bundled edges and then se-
is determined by the bundling layout – thin bundles stay thin. In con-      lecting all edges which contain feature points in the disc. This query
trast, splatting techniques tend to make thin bundles relatively thicker,   is useful for basic edge brushing and for building the next two queries.
which consumes screen space and increases occlusion chances. Sec-           Secondly, we want to select all edges in the most prominent bundle,
ondly, if we relax the bundling as described earlier, individual edges      or bundle branch, passing through the disc. We repeat the basic se-
become visible but still show up as a coherent whole due to the cush-       lection, count the number of selected edges having the same cluster
ion shading. Figure 5 d shows this. To better illustrate the effect, we     id, and retain the ones having the cluster id for which the most edges
decreased here the overall opacity of the edges. The inset shows how        were found. This selects the thickest bundle branch close to the mouse,
bundles appear as shaded profiles even though they are not, techni-         since edges within any bundle branch always have the same cluster ids,
cally speaking, compact surfaces. Thirdly, although we could use a          by construction. Finally, to select an entire cluster, we do the basic se-
physically correct shading model (like [21]), we found our pseudo-          lection and return all edges in the cluster whose id is the one for which
illumination adequate in terms of our goal of understanding overlap-        the most edges were found.
ping bundles.
2.6.3 Interaction                                                           3       I MPLEMENTATION
We have experimented with several types of interactive exploration          Several implementation details are crucial to the efficiency and robust-
atop of our method. In particular, our image-based pipeline and ex-         ness of our method, as follows.

       a) no relaxation or smoothing                      b) smoothing                     c) relaxation and shading                          d) translucency




                                e) smoothing                                                                      f ) relaxation


Fig. 5. Layout postprocessing. Edge smoothing (a vs b, Fig. 7 j vs e). Edge relaxation (Fig. 7 j vs f). Cushion shading (c), half-transparent detail (d)


3.1 Image-based operations                                                              Graph             Tips Points Inflation Holes Skel. Paths Attraction
                                                                                        (I = 5)                           (ms) (ms) (ms) (ms.)         (ms)
We compute shapes, skeletons, skeleton tips, and distance and feature                   US airlines         22 8388                77   120   314     98        20
transforms in an image-based setting. First, we render all edges us-                    US migrations       28 9780                78   134   339    170        77
ing standard OpenGL polylines. Next, we use a Nvidia CUDA 1.1                           Radial              14 21580               80    96   357     45        17
based implementation of exact Euclidean distance-and-feature trans-                     France air          34 23759               81   148   374    222        88
forms [4]. We extended this technique to compute robust skeletons                       Poker               28 2385                64   117   238    146        13
based on the augmented fast marching method (AFMM) in [32]. In                          CUDA implem.                                2     8     2   < 12         3
brief, we arc-length parameterize the shape boundary ∂ Ω and detect
SΩ as pixels whose neighbors’ feature points subtend an arc on ∂ Ω                  Table 2. SBEB performance. Figures are averages for all clusters at it-
larger than a given value ρ . The value ρ indicates the minimal detail              eration I = 5 for different graphs. First rows show CPU timings. Last row
size on ∂ Ω which creates a skeleton point. Since ∂ Ω is a level-set of a           shows CUDA-based timings (which are uniform for the tested graphs).
distance transform at value ω of a set of smooth curves (edges), it only
contains ’sharp’ details at the curve end points. Hence, setting ρ = πω ,           line with [32]). For a graph with 200 clusters (Fig. 7 a-b), this yields
i.e. half the perimeter of a circle of radius ω , guarantees that skele-            80 seconds/iteration. The AFMM is O(δ |C| log(δ |C|)) where |C| is
ton tips correspond to edge end points. The skeletonization method                  the number of pixels on all edges in a cluster C, since the AFMM
choice is essential: the AFMM guarantees that no spurious branches                  computes within a band of thickness δ around its input shape, i.e.
appear due to boundary perturbations, which in turn guarantees stable               |Ω| = O(δ |C|). In contrast, our CUDA implementation takes 4 mil-
bundling cues. However, even if all skeleton tips correspond to edge                liseconds per distance, feature transform, and skeletonization for the
end points, this does not mean that all edge end points correspond to               same image on a Nvidia GT 330M GT card, in line with performance
skeleton tips. Short edges within a large cluster do not produce skele-             reported in [4], i.e. 0.8 seconds per iteration for the graph in Fig. 7 a-
ton tips. This is another reason for using the displacement function φ              b. Graphs with fewer clusters require proportionally less time, since
(Eqn. 8) to guarantee that no edge end points move during bundling.                 the speed of the CUDA method is O(N) for an image of N pixels,
                                                                                    thus image-size-bounded. Overall, the CUDA solution is roughly 100
  Graph             Nodes      Edges       Clusters/iteration       Total (GPU)     times faster than the CPU-based AFMM.
                                         I=1    I=5        I = 10          (sec.)      The complexity of the skeleton path computations (Sec. 2.4) is
  US airlines         235       2099       90       15         9             6.3    discussed next. Following earlier comments on the distance-level-
  US migrations      1715       9780       57       14         7             4.1    set nature of ∂ Ω, the number of skeleton tips |T | for a shape is
  Radial             1024       4021       94       30        24             7.4    O(|∂ Ω|/(πω )). Since we set ω to a fixed fraction of the image size
  France air        34550      17275      207       40        26            29.2    (0.05, see Sec. 2.2), we get on the average a few tens of tips per skele-
  Poker               859       2127       86       28        23             5.2    ton, regardless of the number of edges in a cluster (Tab. 1 (Tips)).
                                                                                    AFMM guarantees 1-pixel-thin skeletons [32], so all nodes in the
          Table 1. Graph statistics for datasets used in this paper                 skeleton pixel-adjacency-graph are of degree 2, except skeleton junc-
                                                                                    tions which are O(|T |) in number. The length of the skeleton of a
   The original CPU-based AFMM [32] is too slow for our task. Ta-                   shape ∂ Ω is O(|∂ Ω|). Hence, the depth-first-search finding of skele-
ble 2 show the inflation (Eqn. 2) and skeletonization times (Eqn. 4),               ton paths between tips (Sec. 2.4) is O(|T |2 |∂ Ω|) using a brute-force
the latter also including the skeleton feature transform, on a 2.8 GHz              method. Table 2 (Paths) shows the costs for the graphs in this paper
quad-core Windows PC (Sec. 4) for several graphs at an image size of                using quad-core multithreading with one depth-first-search per thread.
10242 . Table 1 gives statistics on these graphs, including the (decreas-           The same implementation on CUDA reduces the costs to 12 millisec-
ing) number of clusters at several iterations. On the average, the time             onds (or less for skeletons with fewer tips) as more cores are avail-
needed by the AFMM to process a cluster sums up to 0.4 seconds (in                  able. This cost could be reduced further, if desired, by using the same

depth-first search on the much simpler graph whose nodes are skeleton        how much edges approach the skeleton at one iteration. This implic-
tips and skeleton branch junctions and edge weights given by skeleton        itly controls the bundling convergence speed. Too high values yield
branch lengths, or faster all-pairs shortest path algorithms at the ex-      tight bundles and convergence after the first few iterations, which
pense of a more complex implementation [17].                                 is fine for graphs which already have relatively grouped edges, but
   The attraction step is linear in the number of edge discretization        limits the freedom in decluttering complex graphs. Too low values
points, i.e. tens of thousands for large graphs (Tab. 1 (Points)). Edges     allow the iterative process to adapt itself better to newly discovered
are attracted independently to their cluster skeleton, so CUDA paral-        clusters as the edges approach each other, but convergence requires
lelization of this step is immediate.                                        more iterations. In practice, we set α as a linearly decreasing function
   Inflating edges can produce shapes of genus > 0, i.e. with holes.         of the iteration number from α (0) = 0.9 to α (I) = 0.2.
Technically, this is not a problem, as skeletonization, path computa-
tion, and attraction can handle this. However, we noticed that such          Number of iterations: In practice, after I ∈ [10, 15] iterations, we
holes are rarely meaningful. Holes create loops in the skeleton and          obtain tight bundles of a few pixels in width for all graphs we worked
thus loops in a single bundle, which is supposed to be a tight object.       with. This is expectable, given that (1 − α )I becomes very small
To remove this, we fill all holes in our shapes prior to skeletonization     for α < 1, I > 10. In practice, we always set I = 15 and then use
using an efficient CUDA-based scan fill method, as follows: Given a          smoothing and relaxation to interactively adjust the result as desired.
background seed pixel outside the image Ω, e.g. the pixel (0, 0), we
mark it with a special value v. Next, we fill horizontal scan line seg-      Smoothing: The smoothing amount γs ∈ N describes the number of
ments of background value from each v-valued pixel in parallel, one          Laplacian smoothing steps executed on the bundled layout (Sec. 2.6).
scan line per thread. We repeat alternating horizontal with vertical         Values σs ∈ [3, 10] give an optimal amount of smoothing which keeps
scan line passes until no pixel is filled any more. Checking the stop        the structured aspect of the layout but eliminates the skeleton-like
condition requires only non-synchronized writing to a global boolean         look. Larger values make our layout look similar to the force-directed
variable, set to false before each pass. This parallelizes more effi-        method of [14]. In practice, we noticed that the smoothing amount
ciently than classical scan line or flood fill. Marking all non-v pixels     strongly depends on the task at hand: In some cases, users attach
as foreground fills all holes in Ω. The entire fill takes under 20 scan      semantics to the branching structure, i.e. want to clearly see which
iterations for all images we examined. CUDA filling adds around 8            groups of edges get merged together, so no smoothing is needed. In
milliseconds/image of 10242 pixels in comparison with around 0.15            the general case, however, the exact bundle merging events are not
seconds/image for classical CPU flood fill (Tab. 2 (Holes)) up to a          relevant, so we use by default γs = 5.
total of roughly 25 milliseconds per cluster per iteration. Note that,
due to filling, all skeletons, and thus the created bundles, become trees    Relaxation: The relaxation amount γr ∈ [0, 1] controls the interpo-
rather than graphs. Although we do not use this property now, it may         lation between the fully bundled layout and original one (Sec. 2.6).
enable future interaction work such as user manipulation of the layout       Relaxation is most conveniently applied interactively, after a bundled
by means of bundle handles.                                                  layout has been computed. Values r ∈ [0, 0.2] give a good trade-off
   Clustering using HBA is fast. The CPU implementation in [8] con-          between bundling and overdraw.
structs the complete dendrogram of a graph of 10 to 20K edges in 0.1
seconds on our considered machine. We next added the GPU-based               Overall, the entire method is not sensitive to precise parameter set-
clustering in [5], which is roughly 10 to 15 times faster. Note that only    tings. For the graphs in this paper and other ones we investigated,
a few clustering passes are needed for a complete layout (Sec. 2.5).         we have obtained largely identical bundled layouts with different pa-
Also, we do not need to construct the entire dendrogram, but only the        rameter settings in the ranges indicated above. We explain this by the
bottom-most part thereof, until we reach the cut value δ (Sec. 2.1) at       stability of the inflated shape skeletons to small local variations of the
which we extract the clusters to bundle further.                             positions of edges, and the smoothing effect of the entire iterative pro-
   Finally, postprocessing (Sec. 2.6) poses no performance problems,         cess on the layout. As such, the only two parameters we expose to
so we implement it in real-time using standard OpenGL polyline               users are γs and γr , the others being set to predefined values as ex-
rendering and CPU-based smoothing and relaxation. All in all, the            plained above.
CUDA-based bundling takes 5 to 30 seconds for producing a final lay-
out for the graphs we tested (Tab. 1, right column), i.e. 25 millisec-       4   A PPLICATIONS
onds per cluster times the total number of clusters processed during         We now demonstrate our skeleton-based edge bundling (SBEB)
the I = 10 iterations plus the clustering time. In terms of memory, our      method for several large, real-world, graphs. Statistics on these graphs
method is scalable: we only need a few 10242 images (distance and            are shown in Tab. 1.
feature transforms and skeletons) and discard these once a cluster is            Figure 7 illustrates the SBEB and compares it with several exist-
processed; all paths between skeleton tips for the current cluster; and      ing bundling methods. Note that in all images here generated with our
the graph edge polylines. For all graphs presented here, this amounts        method, we used simple additive edge blending only, as our focus here
to under 100 MB total application memory requirements per graph.             is the layout, not the rendering. Images (a,b) show an air traffic graph
                                                                             (nodes are city locations, edges are interconnecting flights). Images
3.2 Parameter setting                                                        (c,d) show a graph of poker players from a social network. Edges in-
Our entire method has a few parameters: the clustering similarity            dicate pairs of players that played against each other. The node layout
threshold δ , edge advection factor α , total number of iterations I, and    is done with the spring embedder provided by the Tulip framework [3].
smoothing and relaxation amounts γs and γr . These parameters allow          Given the average node degree and node layout algorithm used, related
covering a number of different scenarios, as follows.                        nodes tend to form relatively equal-size cliques. Bundling further sim-
                                                                             plifies this structure; here, bundles can be used to find sets of players
Clustering similarity threshold δ : This parameter specifies the             which played against each other.
granularity level at which we cut the cluster dendrogram to obtain               Images (e-h) show the US migrations graph bundled with the WR,
sets of edges to bundle at the current iteration (Sec. 2.1). We set δ as     GBEB, FDEB, and our method (SBEB) respectively. Overall, SBEB
a linearly decreasing function on the iteration number t ∈ [1, I] from       produces stronger bundling, due to the large number of iterations
δ (0) = 0.95 to δ (I) = 0.7. This yields strongly coherent clusters in       I = 15 being used), and emphasizes the structure of connections be-
the first iteration, regardless of the initial edge position distribution,   tween groups of close cities (due to the skeleton layout cues). If less
and also locally strongly coherent clusters in the subsequent iterations     bundling is desired, fewer iterations can be used (Fig. 4). Adjusting
(Sec. 2.5).                                                                  the postprocessing smoothing and relaxation parameters, SBEB can
                                                                             create bundling styles similar to either GBEB (higher bundle curva-
Edge advection factor α : The advection value α ∈ (0, 1) controls            tures, more emphasis on the graph structure) or FDEB (smoother bun-

                  a)                                     b)                                               c)                              d)




                              e)                                                                     f)




                              g)                                                                     h)




                              i)                                                                     j)

Fig. 7. Air traffic graph (a: original, b: bundled). Poker graph (c: original, d: bundled). US migrations graph (e: FDEB, f: GBEB, g: WR, h: SBEB).
US airlines graph (i: FDEB, j: SBEB). Colors in (a-d,h,j) indicate clusters (displayed for method illustration only)

dles). Finally, images (i,j) show the US airlines graph bundled with             Figure 8 e-g show a citations graph (433 nodes, 1446 edges). Nodes
the FDEB and SBEB respectively. SBEB generates stronger bundling              are InfoVis papers, laid out according to content similarity: close
(more overdraw) but arguably less clutter. Note also that SBEB gen-           nodes indicate papers within the same, or strongly related, topics.
erates tree-like bundle structures which is useful when the exploration       The layout algorithm used for the nodes is multidimensional scaling
task at hand has an inherent (local) hierarchical nature, e.g. see how        with least-square projection [22]. Paper similarity is measured using
traffic connections merge into and/or split from main traffic routes.         cosine-based distance between term feature vectors [26]. Topics were
                                                                              added as annotations to the image to help explanation. Bundling ex-
   Figure 8 shows further examples. The images (a,b) show flight              poses a structure of the citations between topics. We use the bundle-
paths within France, as recorded by the air traffic authorities [15].         based selection (Sec. 2.6.3) to highlight one of the bundles, which
Edge endpoints indicate start and end locations of flight records. The        becomes now dark blue (Fig. 8 f). It appears that this bundle con-
original edges are not straight lines, but actual flight paths (polylines).   nects papers related to the Graph drawing and Treemap topics. The
Note that this dataset is not a graph in the strict sense, since only very    direction of edges is indicated by node label colors: citing papers are
few edge endpoints are exactly identical within the dataset. This has         green, cited papers are blue. Green and blue labels are mixed within
to do with the fact that flight monitoring systems record flights (trails).   this bundle, which is expected, since papers in these two topics typ-
However, edge endpoints are spatially grouped since flights typically         ically cross-reference each other. Figure 8 g shows a selection of all
start and end in geographically concentrated locations such as airports.      edges which end at nodes within the ball centered at the mouse cur-
Given this, our method is able to create a bundled layout of this dataset     sor. Concretely, we highlighted here all papers citing papers in the
with the same ease as for actual graphs. Bundling puts close flight           Graph drawing topic. Note that this selection is a purely node-based
paths naturally into the same cluster. The bundled version emphasizes         one, i.e. it does not use bundles for choosing the edges. However,
the connection pattern between concentrated take-off and landing loca-        bundles have now another use: they allow highlighting specific edges
tions, which are naturally the airports. The zoom-in details (Fig. 8 c,d)     in the graph without increasing clutter, since these edges follow the al-
show the organic effect achieved by bundling.

                                                                                                              c) detail of (a)    d) detail of (b)




                             a)                                       b)


                     virtual worlds               world wide web
          spreadsheets

    volume
    rendering                     UI design


                                                     fisheye views



                                                            graph
                                                            drawing


                                                                                                   graph                                             graph
                                                                                                   drawing                                           drawing
                                                           treemaps                             treemaps
          automated design
                                              algorithm
                             e)               animation                                f ) bundle selection                            g) topic selection


Fig. 8. Bundling of airline trails (a,b) and details (c,d). Bundling of citations graph (e). Selected bundle (in dark blue) shows citations involving two
topics (f). Citations to a selected topic (g). In (f,g), node labels indicate edge direction (citing papers=green,cited papers=blue)

ready computed bundles. Also, note that for this type of node layout,
our clustering-based bundling makes sense: edges will be grouped in           Speed and simplicity: Due to the CUDA implementation of its core
the same bundle if they have similar positions, meaning start/end from        image-based operations, our method is considerably faster than [14]
similar topics; if the node layout effectively groups nodes into related      and slightly faster than [21]. However, we should note that it is not
topics, then bundles have a good chance to show inter-topic relations         clear if the timings reported in [21] include also the cost of comput-
in a simplified manner.                                                       ing the Voronoi diagram underlying the grid graph. The only faster
                                                                              bundled method we are aware of is the MINGLE method [11], which
5   D ISCUSSION                                                               takes 1 second for the US migrations graph and 0.1 seconds for the
In comparison to existing bundling techniques, our method has the             US airlines graph, in contrast to our 4.1 seconds and 6.3 seconds re-
following advantages and limitations:                                         spectively. MINGLE and SBEB share some resemblance in bottom-up
                                                                              aggregation of edges, but also have some differences. MINGLE com-
Generality: Our method can treat directed or undirected graphs. By            pares edges essentially based on end point positions, whereas we use
default, we assume the graph is directed, so edges running between            the entire edge trajectory (which may allow us to bundle graphs with
the same sets of nodes in opposite directions will belong to different        curved edges better). The complexity of MINGLE is O(|E|log|E|) for
clusters, hence create different bundles. For undirected graphs, we           a graph with E edges, whereas SBEB is essentially O(|C|) where C is
only need to symmetrize the edge similarity function (Eqn. 1).                the average cluster size. By using a better cluster selection than our
                                                                              current iso-linkage cut in the cluster tree (Sec. 2.1), it is possible to
Structured look control: Users can control the ’structured look’ of           reduce |C| and thus make SBEB faster.
a bundled layout, ranging between smoothly merging bundles and                   Apart from this, our method works entirely image-based, rather
bundles meeting at sharp angles, by manipulating a single parameter           than manipulating a combination of hierarchical mesh-based and
(smoothing γS , Sec. 2.6). This implicitly allows removing sharp              image-based data structures. The CUDA-based image processing code
ramifications when these are meaningless. Other methods, with the             used by our method is available at [30].
exception of HEB, do not allow explicit control of this aspect, since            Apart from the above, there are several other differences between
there is no explicit hierarchy aspect in the bundles. In our case,            our method and recent edge bundling techniques. In contrast to
hierarchy is modeled by the cluster skeletons (at fine level) and by the      force-directed bundling [14] which bundles pairs of edges iteratively,
progressively simplified cluster structures (at coarse level).                in a point-by-point manner, we bundle increasingly larger groups
                                                                              of edges (our clusters) along their common center in one single
Robustness: Our method operates robustly on all graphs we ex-                 step, using skeletons. In the limit, our method can behave like the
perimented on, i.e. yields a set of stable skeletons and bundles              force-directed bundling, i.e. if we were to treat, at each iteration,
progressively converging towards an equilibrium state. This is                only the most cohesive leaf cluster. However, this is practically not
explained by the regularization of the feature transform (Sec. 2.4) and       interesting, as it would artificially increase the computational cost
the inherent robustness of the skeletonization method used (Sec. 2.3).        without any foreseeable benefits. Further, while Lambert et al. [21]
Briefly put, adding or removing a small number of nodes or edges will         use shortest paths in a node-based grid graph to route edges, in our
not change the bundling since the distance-based shapes are robust to         method edges bundle themselves using only edge information. As
small changes in the input graph and so are their skeletons too.              such, there is no relation between the Voronoi diagrams used in [21]

and our skeletons (which, formally, can be seen as a Voronoi diagram              GRAPH Symp. on Interactive 3D Graphics and Games, pages 134–141,
in which inflated edges are the sites). Distance fields and skeletons             2010.
are also used in [31], but in different ways; first, an edge distance         [5] D. Chang, M. Kantardzic, and M. Ouyang. Hierarchical clustering with
field is computed using a considerably less accurate quad-splat-based             cuda/gpu. In Proc. ISCA, pages 130–135, 2009.
method, whereas our distance transform is pixel-accurate. Secondly,           [6] L. Costa and R. Cesar. Shape analysis and classification: Theory and
skeletons are used as shading cues and not for layout, whereas we use             practice. CRC Press, 2000.
skeletons to actually compute edge layouts. In comparison to [23],            [7] W. Cui, H. Zhou, H. Qu, P. Wong, and X. Li. Geometry-based edge
where bundles split in exactly two sub-bundles, our bundle splits can             clustering for graph visualization. IEEE TVCG, 14(6):1277–1284, 2008.
                                                                              [8] M. de Hoon, S. Imoto, J. Nolan, and S. Myiano. Open source clustering
have in general any degree, as implied by the underlying skeletons.
                                                                                  software. Bioinformatics, 20(9):1453–1454, 2004.
Also, our method can handle general graphs.
                                                                              [9] M. Dickerson, D. Eppstein, M. Goodrich, and J. Meng. Confluent draw-
                                                                                  ings: Visualizing non-planar diagrams in a planar way. In Proc. Graph
Limitations: There is no fundamental reason why a skeleton-based                  Drawing, pages 1–12, 2003.
layout should be preferable to other bundling heuristics, apart from the     [10] G. Ellis and A. Dix. A taxonomy of clutter reduction for information
intuition that a skeleton represents the local center of a shape. Hence,          visualisation. IEEE TVCG, 13(6):1216–1223, 2007.
the quality of our layouts (or any other bundled layout) is still to be      [11] E. Gansner, Y. Hu, S. North, and C. Scheidegger. Multilevel agglomera-
judged subjectively. Moreover, any bundling inherently destroys in-               tive edge bundling for visualizing large graphs. In Proc. PacificVis, pages
formation: edges are overdrawn, so cannot be identified separately;               187–194, 2010.
and edge directions are distorted. Hence, bundling should be used for        [12] E. Gansner and Y. Koren. Improved circular layouts. In Proc. Graph
those applications where one is interested in coarse-scale connectivity           Drawing, pages 386–398, 2006.
patterns and when one cannot apply explicit graph simplification e.g.        [13] D. Holten. Hierarchical edge bundles: Visualization of adjacency rela-
due to the lack of suitable node clustering guidelines and metrics. If            tions in hierarchical data. IEEE TVCG, 12(5):741–748, 2006.
desired, SBEB can be modified to incorporate additional bundling con-        [14] D. Holten and J. J. van Wijk. Force-directed edge bundling for graph
straints e.g. maximal deformation of certain edges - the skeletons pro-           visualization. Comp. Graph. Forum, 28(3):670–677, 2009.
vide only bundling cues but the attraction phase can decide whether,         [15] C. Hurter, B. Tissoires, and S. Conversy. FromDaDy: Spreading data
and how much, to bundle any given edge. In the longer run, it is in-              across views to support iterative exploration of aircraft trajectories. IEEE
teresting to use shape perception results from computer vision [6, 19]            TVCG, 15(6):1017–1024, 2009.
to quantitatively reason about the quality of a bundled layout. Here,        [16] I.Tollis, G. D. Battista, P. Eades, and R. Tamassia. Graph drawing: Al-
                                                                                  gorithms for the visualization of graphs. Prentice Hall, 1999.
our image-based approach may prove more amenable to quantitative
                                                                             [17] G. Katz and J. Kider. All-pairs shortest-paths for large graphs on the
analysis than other bundling heuristics which are harder to describe in
                                                                                  GPU. In Proc. Graphics Hardware, pages 208–216, 2008.
terms of operators having well-known perceptual properties. However,         [18] R. Klette and A. Rosenfeld. Digital geometry: Geometric methods for
this is a challenging task and requires further in-depth study.                   digital picture analysis. Morgan Kaufmann, 2004.
                                                                             [19] I. Kovacs, A. Feher, and B. Julesz. Medial-point description of shape: A
6   C ONCLUSION                                                                   representation for action coding and its phychophysical correlates. Vision
We have presented a new method for creating bundled layouts of gen-               research, 38:2323–2333, 1998.
eral graphs. We exploit the known property of 2D skeletons of be-            [20] A. Lambert, R. Bourqui, and D. Auber. 3D edge bundling for geographi-
ing locally centered within a shape to create elongated shapes from               cal data visualization. In Proc. Information Visualisation, pages 329–335,
                                                                                  2010.
a graph with given node positions, and use skeletons as guidelines to
                                                                             [21] A. Lambert, R. Bourqui, and D. Auber. Winding roads: Routing edges
bundle similar edges. To guarantee the stability and smoothness of
                                                                                  into bundles. Comp. Graph. Forum, 29(3):432–439, 2010.
the bundled layout, we regularize the feature transforms of 2D skele-        [22] F. Paulovich, L. Nonato, R. Minghim, and H. Levkowitz. Least square
tons to eliminate singularities. Using an iterative process, our layout           projection: A fast high-precision multidimensional projection technique
amounts to a sequence of edge clustering and image processing op-                 and its application to document mapping. IEEE TVCG, 14(3):564–575,
erations. We present a CUDA-based implementation which achieves                   2008.
comparable or higher performance than existing edge bundling meth-           [23] D. Phan, L. Xiao, R. Yeh, P. Hanrahan, and T. Winograd. Flow map
ods, but keeps implementation simple. Finally, we present a simple                layout. In Proc. InfoVis, pages 219–224, 2005.
and efficient scheme to emphasize edge bundles using shaded cushion          [24] S. Pizer, K. Siddiqi, G. Szekely, J. Damon, and S. Zucker. Multiscale
techniques computed directly on the bundled edges.                                medial loci and their properties. IJCV, 55(2-3):155–179, 2003.
   We plan next to exploit additional properties of 2D shape skeletons       [25] H. Qu, H. Zhou, and Y. Wu. Controllable and progressive edge clustering
to generate a richer family of bundled layouts. First, by modifying               for large networks. In Proc. Graph Drawing, pages 399–404, 2006.
the Euclidean distance metric underlying the skeleton definition, we         [26] G. Salton. Developments in automatic text retrieval. Science, 253:974–
can generate constrained-angle skeletons which would directly lead                980, 1991.
to layouts similar to cartographic diagrams [29]. Secondly, we plan          [27] K. Siddiqi, S. Bouix, A. Tannenbaum, and S. Zucker. Hamilton-Jacobi
to use bundle-to-bundle and bundle-to-node distance fields to glob-               skeletons. IJCV, 48(3):215–231, 2002.
ally optimize the layout of different edge bundles in order to maxi-         [28] K. Siddiqi and S. Pizer. Medial Representations: Mathematics, Algo-
mize readability and allow for the introduction of spatial constraints            rithms and Applications. Springer, 1999.
                                                                             [29] R. Strzodka and A. Telea. Generalized distance transforms and skeletons
such as labels, bundle crossing minimization, and node-edge overlap
                                                                                  in graphics hardware. In Proc. VisSym, pages 221–230, 2004.
reduction. In the long run, we plan to study the optimality criteria
                                                                             [30] A. Telea. CUDA skeletonization and image processing toolkit, 2011.
of bundled layouts by using existing results from shape perception in             www.cs.rug.nl/˜alext/CUDASKEL.
computer vision which are directly applicable to our skeleton-based          [31] A. Telea and O. Ersoy. Image-based edge bundles: Simplified visualiza-
layout method.                                                                    tion of large graphs. Comp. Graph. Forum, 29(3):543–551, 2010.
                                                                             [32] A. Telea and J. J. van Wijk. An augmented fast marching method for
R EFERENCES                                                                       computing skeletons and centerlines. In Proc. VisSym, pages 251–259,
 [1] J. Abello, F. van Ham, and N. Krishnan. AskGraphView: A large graph          2002.
     visualisation system. IEEE TVCG, 12(5):669–676, 2006.                   [33] F. vam Ham. Using multilevel call matrices in large software projects. In
 [2] D. Archambault, T. Munzner, and D. Auber. Grouse: Feature-based and          Proc. InfoVis, pages 227–232, 2003.
     steerable graph hierarchy exploration. In Proc. EuroVis, pages 67–74,   [34] R. van Liere and W. de Leeuw. GraphSplatting: Visualizing graphs as
     2007.                                                                        continuous fields. IEEE TVCG, 9(2):206–212, 2003.
 [3] D. Auber. Tulip visualization framework, 2011. tulip.labri.fr.          [35] H. Zhou, X. Yuan, W. Cui, H. Qu, and B. Chen. Energy-based hierarchi-
 [4] T. Cao, K. Tang, A. Mohamed, and T. Tan. Parallel banding algorithm          cal edge clustering of graphs. In Proc. PacificVis, pages 55–62, 2008.
     to compute exact distance transform with the GPU. In Proc. ACM SIG-
