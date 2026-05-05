# 05-interactive-level-of-detail-rendering-of-large-graphs

Zuerst ersch. in : IEEE Transactions on Visualization and Computer Graphics : T-VCG. - 18 (2012), 12. - S. 2486-2495
                                                      http://dx.doi.org/10.1109/TVCG.2012.238
2486




                 Interactive Level-of-Detail Rendering of Large Graphs
                               Michael Zinsmaier, Ulrik Brandes, Oliver Deussen, and Hendrik Strobelt




         Fig. 1. Application of our visualization technique on a hierarchical data set, zooming from overview (left) to a region of interest (right).
         The density-based node aggregation ﬁeld (blue color) guides edge aggregation (orange/red color) to reveal visual patterns at different
         levels of detail.

         Abstract— We propose a technique that allows straight-line graph drawings to be rendered interactively with adjustable level of detail.
         The approach consists of a novel combination of edge cumulation with density-based node aggregation and is designed to exploit
         common graphics hardware for speed. It operates directly on graph data and does not require precomputed hierarchies or meshes.
         As proof of concept, we present an implementation that scales to graphs with millions of nodes and edges, and discuss several
         example applications.
         Index Terms—Graph visualization, OpenGL, edge aggregation.




 1     I NTRODUCTION
We present methods for the interactive visualization of large graphs.           ods is given in Section 3, performance considerations are discussed in
We say a graph is large if it ﬁts into video memory but cannot be               Section 4. An interactive system based on the proposed techniques is
rendered as node link diagram without signiﬁcant over-plotting, thus            described in Section 5. We present its interaction paradigms and some
we deﬁne size relative to the computing environment. For the inter-             example applications. Finally, we summarize and propose future work
active exploration of such graphs fast node and edge aggregation is             in Section 6.
needed in combination with efﬁcient rendering in different levels of
detail (LOD). Both is presented in the following. Our techniques en-            2 R ELATED W ORK
able us to show graphs with up to ∼ 107 nodes and up to ∼ 106 edges             We divide the problem of rendering large graphs on (comparatively)
at interactive rates.                                                           small displays into two main problems: dense regions of nodes and
    Lampe and Hauser [20] describe a method for rendering large                 cluttering of edges. While the ﬁrst is the general problem of dense
graphs as density ﬁelds based on a GPU implementation of Kernel                 point sets commonly faced in visualization and computer graphics,
Density Estimation (KDE). Our method extends their technique for                the second problem is more closely related to structure-aware methods
node aggregation by a two-pass seed point rendering that signiﬁcantly           from information visualization and graph drawing.
reduces geometry and scales to large graphs. Furthermore we present
a fast edge aggregation method that derives start- and endpoints of             2.1 Node Visualization Methods
multi-edge representatives from the underlying node density ﬁeld in             Nodes can be displayed as small elements, at minimum a single pixel
image space. Our method is able to render a graph with a given layout           can represent one node. Nevertheless, clutter and over-plotting are
without preprocessing. No auxiliary data structures such as meshes or           common challenges in point data and scatterplot visualizations. One
node hierarchies are needed.                                                    solution to the problem is to slightly displace the nodes to reduce over-
    Our techniques allow to render large graphs on common graphics              plotting on the whole dataset [18]. Alternatively, optical distortion
hardware at interactive rates. In combination with a zoom based user            techniques and zoomable user interfaces can improve the visualization
interface and ﬂexible KDE bandwidth manipulations efﬁcient graph                in a local area [6]. While both methods preserve the distinct node
exploration is possible as well as interactive and intuitive node label-        representation they either distort the shape of node groups [18, 6] or
ing. Additionally, our techniques provides ﬂexible mechanisms to de-            display only parts of the dataset [6].
ﬁne the representation of aggregates by modifying the normalization                Density-based visualizations avoid these problems and can be
function and used colors as described below.                                    applied to large datasets. Density can be measured by dividing the
    The paper is organized as follows. First we describe and discuss            visualization into bins and counting the number of data points that
the related work in Section 2. A detailed description of our meth-              fall into them. This approach is closely related to histograms and
                                                                                color codes or symbols can be used to represent the local density [8].
                                                                                For instance alpha blended scatterplots are an implicit form of this
 • all authors are with University of Konstanz;                                 technique with a bin sizes equal to one pixel and a color encoded
   E-mail: <surname.name>@uni-konstanz.de.                                      density representation. However similar to histograms the bin sizes
                                                                                and binning borders introduce a bias to the visualization. Instead
                                                                                of such discrete density representations basis functions can be used
                                                                                to accumulate the point inﬂuences into a continuous density ﬁeld.
                                                                                Leeuw and Liere [28] propose a GPU-accelerated technique that
                                                                                visualizes accumulated Gaussian basis functions as continuous ﬁeld
        Konstanzer Online-Publikations-System (KOPS)
     URL: http://nbn-resolving.de/urn:nbn:de:bsz:352-246910

                                                                                                                                                  2487


similar to a heat map. Cao et.al. [7] use Kernel Density Estimation on      techniques use a pure implicit aggregation that exists only as visual
nodes to derive a cluster hierarchy which is input to hierarchical edge     pattern in the visualization. The implicit aggregation allows fast
bundling [14].                                                              rendering without preprocessing and the techniques can be applied to
                                                                            streaming data [20].

2.2   Edge Visualization Methods
                                                                            2.3    Discussion of Related Work
In many cases, graphs are visualized as node link diagrams. In addi-
tion to node clutter, such representations suffer also from over-plotting   Bundling approaches, like Gansner et.al. [12] or Hurter et.al. [17], re-
of edges, since such elements cannot be displayed as efﬁciently. Node       duce visual complexity by grouping edge segments to bundles. Lampe
layout algorithms serve as a global solution to untangle node link di-      and Hauser [20] use a line kernel method to visualize an edge density
agrams while distortion techniques provide local improvements, e.g.         ﬁeld. Although using different metaphors, these approaches aim at
ﬁsheye lenses [24] generate more screen space for interesting areas.        highlighting edge patterns. In contrast, we focus on relationship pat-
Furthermore, the drawing paradigm can be altered to be more space           terns between node density clusters. And thus extend the well known
efﬁcient. Becker [5] suggests to draw the links only half the way to        density representation [20, 28] of point data sets with a closely cou-
their targets. These “half lines” reduce edge clutter and crossings but     pled visualization of inter-cluster connections. FacetAtlas [7] relates
make tracking edges more difﬁcult.                                          to this idea, but addresses smaller magnitudes of elements.
   Apart from such improvements for edge rendering it is common to             Similar to Lampe and Hauser our approach operates in image space
shift the focus from single edges to edge aggregates. Such aggregates       for fast processing using OpenGL. The method generates implicit edge
can be loose edge bundles, edge replacements through meta edges             aggregates which appear as a series of pixel values and do not link
or edge density patterns. In either case single connections become          back to the edges they are aggregating. Object space approaches
harder to read but overall patterns become more prominent. The              (like [12]) retain this mapping between explicit edge aggregates and
aggregation strategies are commonly classiﬁed into hierarchical             edges and beneﬁt from additional rendering options (e.g. changes of
methods, conﬂuent drawing, edge bundling techniques, and density            aggregate geometry or per aggregate shading). But image space al-
based methods.                                                              gorithms can reduce the computational complexity and enable us to
                                                                            achieve the required rendering rates for interactive exploration.
   Hierarchical methods deﬁne a pyramid of simpliﬁed versions
of a graph. This pyramid can be constructed by merging nodes                3     M ETHODS
based on graph theoretic measures [13] or geometric clustering [22].        The core of our contribution for visualizing large graphs is a new
The edges are merged to meta edges, which are explicitly deﬁned             density-based node and edge-aggregate representation that addresses
and represented. The approaches are often designed as interactive           the cluttering problem. Our approach works completely in image
systems that allow the user to browse different aggregation levels          space, does not use complex spatial data structures and utilizes var-
by expanding/collapsing nodes. Reducing the amount of visible               ious features of today’s graphics hardware.
elements allows exploration of datasets with several million edges             We start by describing the generation of continuos node density
[4] on current displays. The creation of the aggregates requires            ﬁelds in Subsection 3.1. Such ﬁelds provide an overview of large
ofﬂine computations, except for datasets that already contain natural       amounts of data without neglecting the inﬂuence of a single node.
hierarchies.                                                                Then we propose a hill climbing approach that uses the obtained node
                                                                            density ﬁeld to guide the positioning of aggregated edges in combi-
   Conﬂuent Drawing represents graphs without edge crossings.               nation with the aggregated nodes. Furthermore, Subsection 3.2 ad-
Dickerson et al. [10] present for instance a heuristic algorithm that       dresses a common problem of overdraw-based edge aggregation: col-
replaces clique and biclique edges with an explicit “trafﬁc circle”         ors change at edge crossings and distort the visual appearance. We
aggregation metaphor. However conﬂuent drawing can not be                   solve this problem by a new drawing routine that takes edge orienta-
applied on general graphs and “the complexity of deciding whether           tion into account.
a general graph is conﬂuent or not still remains an open problem” [10].        In the following we refer to nodes and node coordinates in object
                                                                            space, while using pixel and pixel positions to describe elements in
   Edge Bundling techniques share a common metaphor: they join              image space (screen space).
similar parts of edges to bundles. Single nodes and edges remain in
the visualization, while visual bundles highlight higher level patterns.    3.1    Kernel Density Estimation for Node Aggregation
The aggregates are often deﬁned explicit by a hierarchy [14], a mesh        As mentioned above, we use density ﬁelds to visualize node aggre-
[9, 19] or based on clustering techniques [12, 11, 21]. However,            gates. Lampe and Hauser [20] propose a fast algorithm that generates
the standard representation here is implicit with loose bundles of          such ﬁelds by utilizing the features of todays graphics hardware. Their
variable diameter indicating the aggregates [15, 11, 14]. Still there       approach is inspired by kernel density estimation (KDE) and has the
are some exceptions like edge to edge force based implicit bundling         advantage of very naturally aggregating the node details, as Silverman
strategies [15] or ﬂow like explicit representations [21] and clustering    says “..the data will be allowed to speak for themselves...” [25]. In the
based post processing techniques [26]. Edge bundling scales for             following we introduce their method with our adaption and describe
graphs of medium size (∼ 1 − 10k edges), the algorithms are designed        our extensions that allow scaling to large node sets.
to optimize bundling with allowance for non realtime execution.                The 2D kernel density estimator for n data points xi i ∈ 1, 2, .., n is
Gansner et.al. [12] use a proximity graph and an “ink saving” measure       deﬁned as:
to allow fast hierarchical edge bundling of large graphs. Recently,                                           1 n
Hurter et.al. [17] described an iterative approach which operates on                                fKH (x) = ∑ KH (x − xi )                       (1)
                                                                                                              n i=1
a hight ﬁeld created from applying KDE on edge sample points. In
each iteration step, the sample points are moved along the gradients        with kernel function KH . We adjust the formula such that each point
towards local maxima. With each repetition, the kernel bandwidth is         contributes a weight of one at its position and a decreasing inﬂuence
decreased, which sharpens the density ﬁeld and results in tighter and       to its neighborhood. Similar to other publications [20, 28] we choose
more separated bundles.                                                     a 2D Normal Kernel for K with inﬂuence matrix H. For simplicity
                                                                            we use an isotrope inﬂuence of the kernel in all directions and thus
   Density Based approaches transform the discrete node link                can restrict H to multiples of the identity matrix. A scalar parameter
diagram into a continuous representation. Leeuw and Liere [28]              h is used to control the bandwidth of the kernel function. Additive
represent graphs with node density ﬁelds and Lampe and Hauser               blending of textured rectangles is used to determine fKH (x) for each
[20] extend the method to edges, using line kernels. Density based          pixel. Each node coordinate xi is mapped from object space to a pixel

2488


position xi in image space. For every node a geometry shader creates                                   
                                                                                                                                    original nodes
a rectangle at position xi . The rectangle is ﬁlled with a precomputed                                                             and edges
ﬂoating point texture that approximates the kernel function. The con-                                                               cluster cen ers
tribution of the nodes to the density ﬁeld is accumulated with additive                                                             aggregated edges
blending of the rectangles in the rasterization pipeline (Figure 2 (a)).                                                            effect of the
    For large node sets, however, the described method is time inefﬁ-                                                               EvaluationField
cient because the amount of textured rectangles depends linearly on
the number of nodes within the screen area. Therefore, we extend
the method and signiﬁcantly reduce rendering time by binning nearby
                                                                                                    
node coordinates into pixels. Instead of rasterizing multiple rectangles
at the same position, a single weighted rasterization step per bin is then
sufﬁcient to create the same density ﬁeld.                                   Fig. 3. The hill climbing method is shown as a lateral cut of a height
    Typically, binning is done using spatial data structures such as a       ﬁeld (our interpretation of the node density). The original edge points
Point Region Quadtree (PRQ) [23] which provides fast access queries          (indicated in black at the bottom of the ﬁgure) are translated to the near-
while (ofﬂine) construction is cheap (Figure 2 (b)). PRQs represent          est hilltops (blue). The edges cumulate to aggregates (orange) which
a point aggregation hierarchy by recursively dividing the viewport.          connect the cluster centers (hilltops).
When querying the Quadtree, the hierarchy is cut at an appropriate
level of detail and the next smaller aggregation level is returned. How-
ever, in most cases the Quadtree regions do not exactly ﬁt pixel sizes,         We interpret the node density ﬁeld as height ﬁeld and use a hill
thus causing geometric overhead for non-merged nodes. Furthermore,           climbing algorithm to move starting and end points of the edges to the
the induced storage requirements for meta nodes add up to signiﬁcant         highest point of their visual cluster (the local maximum). The edges
amounts for large graphs.                                                    whose start points fall into the same cluster and whose end points share
    Therefore we propose the Seed Point Method, a technique that uses        another cluster are implicitly aggregated. As result, inner-cluster con-
two render-passes: one to merge the nodes in their pixel-sized bins and      nections are vanished while inter-cluster connections are emphasized.
one to create the actual density ﬁeld. In the ﬁrst pass the node coor-       Figure 3 demonstrates the effect. The graph is shown in the lower part
dinates xi are mapped to pixel positions xi of an Accumulation Field.       of the ﬁgure. The original edges are given in black while the aggre-
The Accumulation Field is a frame buffer object (FBO) in screen res-         gated versions are in orange. The density ﬁeld is shown as hills in the
olution. Node coordinates that fall into the same pixel position are         upper part. The blue points are the aggregate edge points, the orange
cumulated by additive blending.                                              edges the remaining aggregate edges. The edge points correspond di-
    After the ﬁrst render pass, the value of each pixel therefore repre-     rectly to the highest peaks in the node aggregate visualization.
sents the amount of accumulated nodes within its screen space area.             Generally, hill climbing moves points towards a local maximum
The second render pass binds the Accumulation Field as a texture and         which is what we want. If the density ﬁeld contains several small
creates a weighted textured rectangle for every pixel of value ≥ 1 using     local maxima within a large plateau, the corresponding “inner-cluster”
a Geometry Shader (Figure 2 (c)). Doing so, our approach determines          edges are drawn. To avoid this line clutter within plateaus, the KDE
for a given viewport resolution the optimal input set to create a density    bandwidth h can be adjusted to retrieve less edges.
ﬁeld and minimizes the overhead during the kernel blending. More-               As mentioned above, hill climbing is implemented in OpenGL:
over it does not need any additional storage and ﬁts directly into the       The Accumulation Field (see Seed Points method) is bound as tex-
OpenGL pipeline.                                                             ture tAF and a fragment shader operates on this texture as shown in
                                                                             algorithm 1. Within the Accumulation Field for every start pixel the
                                 Direct                                      associated hilltop-pixel is searched by iteratively tracking 3x3 neigh-
                    a
                                                                             borhoods. As starting points we use every pixel that accumulates at
                                                                             least one node. The result of this step serves as input for a geometry
                                                                             shader that repositions the points on the GPU towards the hilltop posi-
                               Quadtree                                      tions. The outcome of the process is an edge aggregation texture where
                b                                                            each pixel value represents the number of edges that pass through it.
                                          pixel size
                                                                             Algorithm 1 Hill climbing in image space
                               Seedpoint
            c
                                                                             Require: texture tAF of the Accumulation Field
                                 1
                                                                               for all pixel positions p ∈ tAF do
                                                                                  ptemp ← p
                    2
                                                                                  if value(ptemp ) = 0 then
                                                                                      run ← true
                                                                                      while run do
Fig. 2. Rendering KDE kernel textures for points in a dataset to create a               K ← 3x3 neighborhood of ptemp
continuous density ﬁeld. a) the direct approach: place a texture for each                pmax ← pixel position in K with highest value
point; b) use a pre-calculated Point Region Quadtree to bin points; c) the
                                                                                        if pmax = ptemp then
Seed Point method uses a two-pass rendering to ﬁrst accumulate points
                                                                                            ptemp ← pmax
per pixel and secondly uses a geometry shader to render parametrized
kernel textures.
                                                                                        else
                                                                                           run ← f alse
                                                                                        end if
3.2 Hill Climbing for Edge Aggregation                                                end while
                                                                                  end if
In the next step we use the node Accumulation Field as input for a new            assign ptemp as hilltop to p
edge aggregation approach that is visually coupled to aggregated node          end for
clusters. Our method bases on the idea that the aggregation of edges
between peaks of the node ﬁeld is an intuitive visual metaphor. In
contrast to other edge aggregation techniques our technique operates            It is important to note that the algorithm does not return explicit
in image space and therefore does not rely on precomputing supporting        meta edges but aggregation results for the edges in form of pixel
data structures.                                                             values. Along with these aggregation results, three visualization

                                                                                                                                                         2489


challenges arise: I) handling of edges that leave the viewport, II)                         
the rendering of approporiate line widths, and III) avoiding visual                                                               
hotspots on edge crossings. While the ﬁrst problem only relates to                                                                   
our method, the latter two are of general interest for density based
methods. We present solutions for all of them in the following.
                                                                                                  
   Edges that leave the viewport: In a simple implementation the                                                                        
Accumulation Field would not be deﬁned outside the viewport and                                                                            
thus edges that leave the visible area would not be aggregated. The
rendering subsequently becomes unstable and panning operations may
alter edge aggregates. These problems are reduced by aggregating
nodes beyond the viewport borders: we suggest combining the visible
                                                                                       a) Euclidean distance              b) Pseudo-Euclidean distance
Accumulation Field with an off screen ﬁeld four times the visible
area. Since this context is not visible and only used for aggregation
we can work with a reduced resolution of the Accumulation Field                Fig. 4. Euclidean and Pseudo Euclidean distance functions used for
outside the screen window. Using half of the resolution outside the            widening edges. The aimed line width in the given example is two, i.e.
visible window only doubles the total node aggregation costs but               width(value(red pixel )) = 2. For the symmetric Euclidean distance the left
                                                                               and right pixels are colored (they have distance 1). For the Pseudo Eu-
is already sufﬁcient to stabilize the edge renderings of most graphs
                                                                               clidean distance only the left pixel is colored, the right pixel has distance
against panning and feathering out at the visible borders.
                                                                               2 and fails the selection criterion 2 ≤ 22 .
   Rendering of thick edges: Edge coloring based on overdrawing
is a common way to visualize aggregate weights in implicit edge rep-
resentations. In contrast to explicit techniques the geometry of the           a max value ﬁlter to eliminate the crossing artifacts (Figure 5 middle
aggregate cannot be altered here. In particular, it is not possible to         and right).
render important edge aggregates with thicker lines because they con-             This technique is implemented in OpenGL by adding two render
sist of many over-plotted single edges and the rendering pipeline is           passes. In the ﬁrst pass the edges of four different angle segments
not able to generate links between edges and aggregates. Therefore all         are rendered into the four separate color channels of a texture. The
edges are treated equally and are rendered with the same line width.           second pass uses a maximum ﬁlter to merge the obtained texture with
   We therefore propose a post-processing step using a fragment                the edge aggregation texture. We suggest using 180 angle segments of
shader that alters line thickness on the edge aggregate texture and            one degree (45 texture runs) for an undirected graph.
creates the illusion of explicit aggregate deﬁnitions. We deﬁne a dis-         4 M EASURES & C OMPLEXITY
tance function dist(pi , p j ) between two pixels pi and p j and a function
width(value(px )) which maps a pixel value to a speciﬁc edge width.            The presented visualization system is based on image operations that
To determine the color of a pixel pi the shader inspects a w × w neigh-        are executed in parallel on the GPU. Moreover, many render opera-
borhood S of pixel pi . All pixels p j ∈ S which fulﬁll the following          tions build upon cheap texture transformations and in particular only
condition are further considered as candidates for coloring:                   three rendering steps depend on the input data. For each node a sin-
                                                                               gle point has to be added to the AccumulationField, each edge has
                                        width(value(p j ))                     to be rendered to the edge aggregation texture and the kernel rectan-
                    dist(pi , p j ) ≤                                   (2)    gles have to be created. The last step depends on the number of Seed
                                               2
                                                                               Points, which is limited by min(#pixels, #nodes). We denote the con-
Among the candidates the shader chooses the p j with the highest value         stant render cost for one Seed Point with Rs , for one rectangle with Rr
to use it for coloring of pi . Using the maximum as selection criterion        and for one edge with Re . The worst case complexity for p pixels, n
implies that important lines are rendered on top of others. The param-         nodes and m edges is deﬁned as:
eter w deﬁnes the size of the neighborhood and thresholds the maximal
line-width. We chose a value of 5 to be sufﬁcient for our approaches.                             O(n · Rs + min(n, p) · Rr + m · Re )                   (3)
   A natural choice for a distance function dist(di , d j ) would be the       Thus we are able to maintain a linear dependency towards the size
Euclidean distance. However, the symmetric character only allows               of the input data. Moreover, the architecture of GPUs compensates for
uneven edge widths of one, three, ﬁve, etc. Therefore we propose an            growing data sizes through parallelization. In practice, nearly constant
asymmetric pseudo Euclidean distance function that shifts the edge             render times can be achieved for graphs with up to ∼ 106 edges on
centers slightly from their intended positions but complements the vi-         common hardware (Figure 6).
sualization with even edge widths. Figure 4 describes the distance                Table 1 gives an overview of the test datasets and measured results.
functions.                                                                     The US air-trafﬁc and US migration graph are well known examples
   For example, given a pixel at position (xe , ye ) and an attached edge      for edge bundling algorithms. The US census [27] data set provides
width of two. Measuring with Euclidean distance, the pixel to the left         more migration data with weighted edges and at a bigger scale. Wiki-
(xe − 1, ye ) and to the right (xe + 1, ye ) would be colored, resulting in    Vote, Net50 and Net150 are available at the Sparse Matrix Collection
a width of three. Using our pseudo Euclidean distance, only the left           [2] and have been laid out with SFDP[16] to allow fair comparison to
pixel (xe − 1, ye ) would be colored. The distance of the right pixel          results of MINGLE. The 4.5M graph and H3 graph (Figure 1) are arti-
(xe + 1, ye ) is two and therefore it does not satisfy the initial condition   ﬁcial test datasets for edge aggregation and the Europe dataset serves
of equation 2: 2 ≤ 1.                                                         as node rendering benchmark. The latter one has been extracted from
                                                                               OpenStreetMap [1] and includes one point for each tagged building.
   Avoiding hotspots on edge crossings: Measuring the overdraw for                Figure 6 compares the presented approach to the results of MIN-
computing edge widths and colors works well for isolated edges. If             GLE [12] and KDEEB [17], two of the, to our knowledge, fastest al-
multiple aggregates cross the same pixel, however, all involved edges          gorithms for edge bundling. To allow a comparison to KDEEB on
accumulate. Edge crossings therefore become hotspots and produce               large data sets we include a random graph of the same size as de-
disturbing artifacts in the visualization. Moreover the density peaks          scribed in [17]. The random graph is marked explicitly because of it’s
distort the normalization for color mapping and width assignment and           unusual properties: two times more nodes than edges and quasi-equal
constrain the visualization space for actual edges (Figure 5 left).            node distribution . Overall the diagram shows a roughly linear corre-
   We propose to render edges separated by angles to reduce artifacts          lation between the number of edges and the render time for MINGLE.
of edge crossings. The result is a set of textures that is merged with         The results for KDEEB are more difﬁcult to interpret but the authors

2490




                                                               a) with hotspots                                             b) hotspots removed with             c) hotspots removed with
                                                                                                                            angle separated rendering           angle separated rendering
                                                                                                                                                                and color scaling corrected


Fig. 5. (a) Edge crossings become hotspots and distort the coloring and edge widening. (b) Angle separated rendering removes the artifacts, (c)
color scaling and edge widths assignment is corrected.


Table 1. Rendering times in seconds. The marked columns (*) have been reported in [12] (CPU approach) and in [17] (GPU GTX 580). The
remaining columns measure the average GPU time to create an overview of the whole graph (left) for 32px and 128px kernel size. The worst
rendering times found by manual inspection are given at the right columns. Resolution is 1500x750 pixel.
                                                                                                description                                          overview                           bad case
                                          dataset                        source                    #nodes    #edges                 MINGLE*         KDEEB* 32px          128px       32px 128px
                                          US air-trafﬁc                    [3]                        275     1,925                      0.1             0.5  0.3           0.3        0.3      0.3
                                          US migration                      /                        1702      9780                      1.0             1.5  0.2           0.3        0.4      0.4
                                          Wiki-Vote                        [2]                      8,436   103,660                     18.4                / 0.3           0.4        0.3      0.5
                                          random graph                      /                     200,000   100,000                        /            18.0  0.4           2.2        0.4      2.2
                                          net50                            [2]                     16,320   464,440                     87.1                / 0.4           0.4        0.4      0.4
                                          US census                       [27]                       3075   545,882                        /                / 0.5           0.5        0.6      0.6
                                          net150                           [2]                     43,517 1,538,840                    355.0                / 0.4           0.4        0.7      0.8
                                          4.5M                              /                      99,965 4,551,564                        /                / 1.2           1.2        2.1      2.5
                                          Europe                           [1]                 37,612,093         /                        /                / 0.2           0.5        0.4      2.4



                                                               edge dependence
                                                                                                                                        and the render costs for edges have the highest impact on the overall
                                                                                                                                        performance and we therefore discuss these factors in the following:
              1000
                                                                                                           net150




                                                                                                                                           Kernel Rasterization: The costs for kernel rasterization depend on
                                                                                               net50
                                                                                   Wiki-Vote




                                                                                                                                        the number of Seed Points and the size of the rectangles. The amount
                                                                   random graph




                                                                                                                       MINGLE
                          US airtraf ic




                    100
                                                                                                                                        of Seed Points is difﬁcult to estimate because it depends on the current
  time in seconds




                                                                                                                       KDEEB
                                                US m gration




                                                                                                                       LaGO             viewport and the image resolution. The above discussed border of
                     10
                                                                                                                                        min(#pixels, #nodes) is used as upper limit. In practice, real world
                                                                                                                                        datasets normally do not have a uniform node distribution (i.e. not all
                                                                                                                                        pixels contain nodes) and the actual number of rectangles is thus often
                      1                                                                                                                 much smaller than the amount of pixels or nodes. In the following
                                                                                                                                        we will speak of a weak linear dependency that is relevant for some
                                                                                                                                        data sets like the artiﬁcial random graph but often overestimates
                    0.1                                                                                                                 the problem (e.g. Europe data set). We provide measurements of
                      1e+03                    1e+04                              1e+05                1e+06        1e+07               an “overview” and a “bad case” viewport to illustrate the viewport
                                                                 number of edges
                                                                                                                                        effects on our test data (Table 1). The second factor (the size of
                                                                                                                                        the rectangles) relates quadratically to the selected bandwidth h and
                                                                                                                                        determines the texturing costs for the kernels. Table 1 and ﬁgure 6
Fig. 6. Log-log scale comparison of the results reported for MINGLE                                                                     show results for a small kernel with diameter of 32px and a large
[12] and KDEEB [17] with the presented approach (128px kernel). The                                                                     variant with 128px.
GPU implementation allows our approach to maintain nearly constant
rendering times below one second up to a graph size of ∼ 106 edges on
                                                                                                                                           Rendering of Edges: The texture for the edge aggregation is cre-
real world data. The two marked data points refer to the artiﬁcial random
dataset with special properties.
                                                                                                                                        ated by the already described angle-separated rendering of all edges of
                                                                                                                                        the current viewport. The costs for edge rendering depend linearly on
                                                                                                                                        the amount of edges m with a constant factor for the overhead caused
                                                                                                                                        by our multi-pass rendering technique.
state that they achieve about the same speed as MINGLE for larger                                                                          Despite the weak (nodes) and strong (edges) linear dependencies
graphs and a linear correlation can thus also be assumed. In contrast,                                                                  on the data size the image based design of our approach allows us to
our algorithm achieves nearly constant results for all datasets ≤ 106                                                                   maintain near constant render times for large graphs and also point
edges.                                                                                                                                  datasets. At some point, however, the hardware limits are reached and
   Our test system consists of a high end consumer graphics board                                                                       parallelization is no longer able to compensate the growth of data. On
(Nvidia GTX590) and an i7 - 2600K CPU. The critical factor, how-                                                                        today’s consumer hardware our approach scales well to graphs with
ever, is the GPU performance and similar results can be achieved with                                                                   ∼ 106 edges or point datasets with ∼ 107 nodes. Additionally it would
several ATI graphics cards (HD6950 +).                                                                                                  be straight forward to distribute the render steps on multiple GPUs to
   An analysis of our measurements, the shader code and the outlined                                                                    deal with even bigger problem spaces.
data dependencies shows that the rasterization of the kernel rectangles

                                                                                                                                                 2491


5     A PPLICATIONS                                                         different airports of the San Francisco Bay Area and their individual
In this section we describe LaGO (Large Graph Observer), an imple-          connections to LA, which sum up to approximately one percent of all
mentation of our methods and give examples of data sets visualized          ﬂights in July 2011. In contrast to the edge density visualization of
using the tool.                                                             Lampe and Hauser [20], the integration of nodes has the advantage
                                                                            that airports and their relative importance can be clearly spotted in our
5.1    LaGO                                                                 visualization and edge crossings with high densities cannot be misin-
                                                                            terpreted as airports.
LaGO provides zoom and pan operations to support the interactive
exploration of visualized graphs. Similar to related density based ap-      US migration data
proaches [20, 28] the bandwidth parameter h is bound to the viewport        Figure 9 and ﬁgure 10 visualize US migration data. The ﬁrst data set
to support semantic zooming. For instance increasing the zoom level         is commonly used to depict the effects of edge bundling algorithms
shrinks the viewport such that a smaller subset of the data is displayed    (e.g. [17]) and consists of 9,780 unweighted edges. In contrast the
and reduces the bandwidth (world space) to decrease the aggregation         second data set is much larger with 545,882 weighted edges and 3075
level. However, we not only shrink and expand the node clusters but         nodes. It is based on the Census 2000 and contains all county-to-
also adjust the closely integrated edge aggregates.                         county migration ﬂows in the United States between 1995 and 2000
   The interactive exploration leads to large variations of the visual-     [27]. Figure 9 shows strong migration ﬂows at the East Coast and in
ized density values and ﬁxed color mapping cannot address sparse and        the South West of the United States. Moreover there are strong con-
crowded viewports equally. We therefore provide an automatic nor-           nections near big cities like Chicago, Denver, Atlanta and Housten.
malization of the densities with the maximal value of the current view-     While these patterns get also highlighted in most edge bundling vi-
port. The normalized density values are in the interval [0..1] and we       sualizations there remain interesting differences. The presented ap-
use them as texture coordinates such that the density to color mapping      proach aggregates edges solely based on their start and end points and
can be deﬁned with free choosable color schemes.                            near parallel edges are therefore often not aggregated. For instance
   The automatic normalization is convenient, however in some cases         the East to West pattern which is strongly highlighted in bundling ap-
more control may be desirable for instance to maintain a consistent         proaches like FDEB [15] and Winding Roads [19] is less obvious in
color mapping during pan operations. We therefore provide an inter-         our visualization. However the clear mapping between aggregates and
face for manual ﬁne control that can be used to lock the normalization      their start and end clusters makes it easier to verify actual connec-
devisor or to set it to a speciﬁc value. If a ﬁxed devisor overshoots the   tions like New York ⇔ Florida. The second migration data set (Figure
normalization interval the system clips the results and indicates the       10) has been rendered with edge weights equal to the number of total
potentially misleading color-mapping to the user by highlighting the        movements between the different counties. Interestingly the weights
lock symbol.                                                                emphasize short cluster connections like those near Los Angeles, Dal-
   The distribution of aggregated items might be uneven and hotspots        las and Boston. One explanation for these patterns could be a tendency
skew the normalization. We therefore provide a graphical user inter-        towards local movements. For instance nine of the top ten connections
face that allows the application of scaling functions to the linear nor-    are between neighboring counties.
malized values. Normalization, scaling and the value to color mapping
can be used in combination to ﬁlter the data and balance weak against
strong visualization elements.
   The described viewport control and ﬁlter mechanisms allow the ex-
ploration of large graphs at variable levels of detail. However apart
from geometry and connectivity information graph datasets often con-
tain node names. LaGO therefore provides a detail on demand imple-
mentation that allows the interactive labeling of the node density ﬁeld.
The hill climbing approach from the edge aggregation can be used to
group the nodes according to their cluster center and provides an in-
tuitive cluster deﬁnition for prominent areas in the visualization. The
user selects a cluster by clicking onto it and the system retrieves the
cluster nodes and sorts them according to their degree or a dedicated
weight. Subsequently a list of the most prominent labels is displayed
and the user selects labels from the list to annotate the cluster nodes     Fig. 9. US migration data set of recent publications visualized in LaGO.
(Figure 7).

5.2    Examples                                                             Net 50 data
US air-trafﬁc data                                                          To enable a visual comparison with MINGLE; we applied our visual-
Figure 7 shows an application of our method to the US air-trafﬁc data       ization to the Net50 data set (Figure 11). Our method reveals that the
set. We selected all ﬂights in the US from July 2011 (≥ 500.000) and        half-ring on the right side (I) connects homogeneously to cluster II. No
boiled them down to 1925 distinct connections. These connections            signiﬁcant connection from the upper part of the half-ring (I) connects
are interpreted as undirected weighted edges to create the visualized       to the lower part of the cluster and apart from one outlier all con-
graph. The weight of an edge is equivalent to the the number of ﬂights      nections end on the right side of cluster II. The cluster itself has two
on the connection and the weight of a node is the sum of the connected      highly interconnected peaks that seem to be the end points for most
edge weights. The color scaling for edge and node aggregates is non         of the connections from the rectangular cluster (III). Within cluster III
linear, as can be seen on the scaling bars in the right lower corner.       the connections reveal a cross pattern, the edges entering from the right
Furthermore the open lock, above the scaling bars, indicates that the       side are connected to the left half of the ﬁeld and vice versa. Addition-
automatic normalization of data values is active. The applied color         ally, the small outer clusters on the right side of the half-ring (I) are
scheme focusses on strong edges, while small edges are attenuated by        not equally distributed and the main connections go to the half-ring (I)
transparency. The prominent ﬂight hubs (Atlanta, Chicago, LA, San           and not to other parts of the graph. The described patterns are harder to
Francisco, East coast) appear immediately and strong connections like       read from the MINGLE visualization [12] because the x-shaped edge
LA ⇔ San Francisco are marked by color and width. When zooming              aggregates hinder tracking of connections and pure bundling cannot
in (i.e. reducing the bandwidth) the aggregates split and smaller air-      sufﬁciently reduce the complexity of dense edge clusters. For instance
ports like San Diego in the LA area or Sacramento near San Francisco        the homogenous characteristics of the half ring cannot be spotted and
appear (Figure 8). The most detailed view reveals ﬁnally the three          cluster II appears as crowded heat balls in the visualization.

2492




Fig. 7. US air trafﬁc data set. The node aggregation highlights important ﬂight hubs, while edge aggregation shows e.g. a dense connection
between Los Angeles and San Francisco. A click in the Miami area (low right) highlights important nodes and a label list on the top left. From the
list the user can choose interesting labels, that are placed within the visualization. The color mapping scale is shown on the bottom right.




Fig. 8. Semantic zoom into the San Francisco Bay Area. The leftmost picture displays a high aggregation level where all airports in the region
around San Francisco and LA get merged. Zooming in reveals smaller nearby airports like Sancramento and San Diego however the main
connection remains between the two big cities. The rightmost picture shows ﬁnally the three Bay Area airports and their individual connections.

                                                                                                                                                 2493




Fig. 10. US census data set with 545,882 weighted edges depicting the county-to-county migration ﬂow between 1995 and 2000. A zoomed per-
spective (right lower corner) shows connections between single counties while the overview aggregates nearby clusters and allows the observation
of higher level patterns like the connection between New York and Florida.




                                                                                                  I




                                                 III




                                                                                    II




Fig. 11. The Net 50 data set with the color scheme provided bottom left. The visualization reveals several interesting properties of the dataset. For
instance the homogeneously structure of the connection from the half-ring (I) to cluster II, the edge cross patterns in cluster III or the two highly
interconnected central peaks in cluster II.

2494


Random data
Figure 12 shows a random graph with 200,000 nodes and 100,000
edges which is similar to an example given in Hurter et.al. [17]. Two                                                    Arc de Triomphe
snapshots are given for smaller (left) and larger (right) KDE band-
width. It can be seen, that in both aggregation levels no obvious pat-
tern occur. Since the graph is random and reﬂects a quasi-equal dis-
tribution, Fig. 12 can be seen as a valid representation which avoids
false positive graph patterns. The graph is also an extreme case for
our method as its nodes are nearly equally distributed over the canvas.
This reduces rendering speed, because nearly every node occupies an
own pixel and therefore becomes a seed point for a KDE texture (see
Section 4 and Table 1).




Fig. 12. A random graph with 200,000 nodes and 100,000 edges (simi-                                        Europe
lar to the example in [17] ). While bandwidth h is increased no patterns
occur; an effect wanted to avoid false positive patterns.                  Fig. 13. Interactive zoom into the Europe dataset with 37.6 million nodes
                                                                           that represent all tagged buildings from OpenStreetMap. The highest
                                                                           aggregation level shows interesting data quantity differences at state
OpenStreetMap data                                                         borders. Zooming into Arc de Triomphe area reveals scenic and archi-
Figure 13 visualizes the Europe point dataset that has been extracted      tectural patterns (e.g. street structure).
from OpenStreetMap. The data contains one node for each tagged
building in Europe, a total of 37.6 million distinct nodes. The dis-
cussed improvements of the node rendering approach allow the inter-
active exploration of this dataset even on a low end consumer graphics
card (ATI HD5770).

6 C ONCLUSION & F UTURE W ORK
We have presented an new approach that integrates node density aggre-
gation and meta edge generation for the visualization of large graphs at
different levels of detail. The methods are optimized for fast process-
ing in OpenGL to allow interactive rates when using common graph-
ics hardware. We showed that by using a two-pass rendering method,
node aggregation can be accelerated without signiﬁcant memory cost.
The edge aggregation on top of the node density ﬁeld and the proposed
methods for post-processing allow fast rendering of implicit edge ag-
gregates with the look of explicit meta edges.
   The methods are implemented in a software tool that is used for
applying our approach to large datasets . The tool allows panning
and zooming at interactive rates and is highly conﬁgurable w.r.t color
mapping and normalization scaling functions.
   For future work, we plan to investigate if for a given zoom level a
best kernel size can be estimated dynamically. Therefore we want to
conduct a user study to evaluate what will be a best visualization for
different zoom levels. We furthermore plan to release a free version of
the described software tool.

ACKNOWLEDGMENTS
We thank Arlind Nocaj, Mirza Klimenta, and Christophe Hurter for
support with data sets. This work has been funded in part by Deutsche
Forschungsgemeinschaft (DFG) under grant GK-1042, Explorative
Analysis and Visualization of Large Information Spaces, Konstanz.          Fig. 14. Wiki-Vote data set laid out with an MDS algorithm. Note that
                                                                           our rendering reveals a prominent bipartite core rather than producing
                                                                           the usual clutter in the center of a small-world graph.

                                                                                                                                                      2495


R EFERENCES                                                                       [27] U.S. Census Bureau.         County-to-county migration ﬂow ﬁles.
                                                                                       http://www.census.gov/population/www/cen2000/
 [1] Openstreetmap. http://openstreetmap.de/, Jul 2011.                                ctytoctyflow/, June 2012.
 [2] Sparse matrix collection.             http://www.cise.ufl.edu/               [28] R. van Liere and W. de Leeuw. Graphsplatting: Visualizing graphs as
     research/sparse/matrices/, Jan 2012.                                              continuous ﬁelds. IEEE Transactions on Visualization and Computer
 [3] Us airtrafﬁc dataset. http://www.transtats.bts.gov/, Jan                          Graphics, 9(2):206–212, Apr. 2003.
     2012.
 [4] J. Abello, F. van Ham, and N. Krishnan. ASK-GraphView: A large
     scale graph visualization system. IEEE Transactions on Visualization
     and Computer Graphics, 12(5):669–676, 2006.
 [5] R. A. Becker, S. G. Eick, and A. R. Wilks. Visualizing network data.
     IEEE Transactions on Visualization and Computer Graphics, 1:16–28,
     1995.
 [6] T. Buering, J. Gerken, and H. Reiterer. User interaction with scatterplots
     on small screens - a comparative evaluation of geometric-semantic zoom
     and ﬁsheye distortion. IEEE Transactions on Visualization and Computer
     Graphics, 12(5):829–836, Sept. 2006.
 [7] N. Cao, J. Sun, Y. Lin, D. Gotz, S. Liu, and H. Qu. Facetatlas: Multi-
     faceted visualization for rich text corpora. Visualization and Computer
     Graphics, IEEE Transactions on, 16(6):1172–1181, 2010.
 [8] D. B. Carr, R. J. Littleﬁeld, W. L. Nicholson, and J. S. Littleﬁeld. Scat-
     terplot matrix techniques for large n. Journal of the American Statistical
     Association, 82(398):pp. 424–436, 1987.
 [9] W. Cui, H. Zhou, H. Qu, P. C. Wong, and X. Li. Geometry-based edge
     clustering for graph visualization. IEEE Transactions on Visualization
     and Computer Graphics, 14(6):1277–1284, Nov. 2008.
[10] M. Dickerson, D. Eppstein, M. Goodrich, and J. Meng. Conﬂuent draw-
     ings: Visualizing non-planar diagrams in a planar way. In G. Liotta,
     editor, Graph Drawing, volume 2912 of Lecture Notes in Computer Sci-
     ence, pages 1–12. Springer Berlin / Heidelberg, 2004. 10.1007/978-3-
     540-24595-7 1.
[11] O. Ersoy, C. Hurter, F. Paulovich, G. Cantareiro, and A. Telea. Skeleton-
     based edge bundling for graph visualization. IEEE Transactions on Visu-
     alization and Computer Graphics, 17(12):2364–2373, Dec. 2011.
[12] E. R. Gansner, Y. Hu, S. North, and C. Scheidegger. Multilevel agglom-
     erative edge bundling for visualizing large graphs. In Proceedings of
     the 2011 IEEE Paciﬁc Visualization Symposium, PACIFICVIS ’11, pages
     187–194, Washington, DC, USA, 2011. IEEE Computer Society.
[13] E. R. Gansner, Y. Koren, and S. C. North. Topological ﬁsheye views for
     visualizing large graphs. IEEE Transactions on Visualization and Com-
     puter Graphics, 11(4):457–468, July 2005.
[14] D. Holten. Hierarchical edge bundles: Visualization of adjacency rela-
     tions in hierarchical data. IEEE Transactions on Visualization and Com-
     puter Graphics, 12:2006, 2006.
[15] D. Holten and J. J. Van Wijk. Force-directed edge bundling for graph
     visualization. Computer Graphics Forum, 28(3):983–990, 2009.
[16] Y. F. Hu. Efﬁcient and high quality force-directed graph drawing. The
     Mathematica Journal, 10:37–71, 2005.
[17] C. Hurter, O. Ersoy, and A. Telea. Graph bundling by kernel density
     estimation. Computer Graphics Forum (EuroVis 2012), 31(3):865 – 874,
     2012.
[18] D. A. Keim, M. C. Hao, U. Dayal, H. Janetzko, and P. Bak. Generalized
     scatter plots. Information Visualization, 9:301–311, December 2010.
[19] A. Lambert, R. Bourqui, and D. Auber. Winding roads: Routing edges
     into bundles. Computer Graphics Forum, 29(3):853–862, 2010.
[20] O. D. Lampe and H. Hauser. Interactive visualization of streaming data
     with kernel density estimation. In Proc. IEEE Paciﬁc Visualization Symp.
     (PaciﬁcVis), pages 171–178, 2011.
[21] D. Phan, L. Xiao, R. Yeh, P. Hanrahan, and T. Winograd. Flow Map
     Layout. Proceedings of the 2005 IEEE Symposium on Information Visu-
     alization, 0:29+, 2005.
[22] A. Quigley and P. Eades. FADE: Graph Drawing, Clustering, and Visual
     Abstraction. In GD ’00: Proceedings of the 8th International Symposium
     on Graph Drawing, pages 197–210, London, UK, 2001. Springer-Verlag.
[23] H. Samet. The quadtree and related hierarchical data structures. ACM
     Comput. Surv., 16:187–260, June 1984.
[24] M. Sarkar and M. H. Brown. Graphical ﬁsheye views of graphs. In
     Proceedings of the SIGCHI conference on Human factors in computing
     systems, CHI ’92, pages 83–91, New York, NY, USA, 1992. ACM.
[25] B. Silverman. Density estimation for statistics and data analysis. Mono-
     graphs on statistics and applied probability. Chapman and Hall, 1986.
[26] A. Telea and O. Ersoy. Image-based edge bundles: Simpliﬁed visualiza-
     tion of large graphs. Computer Graphics Forum, 29(3):843–852, 2010.
