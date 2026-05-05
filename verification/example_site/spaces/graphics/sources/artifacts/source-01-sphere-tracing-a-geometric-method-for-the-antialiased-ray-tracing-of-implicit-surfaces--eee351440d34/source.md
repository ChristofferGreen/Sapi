# 01-sphere-tracing-a-geometric-method-for-the-antialiased-ray-tracing-of-implicit-surfaces

Pratique mathématiques de l’art numérique : le shadercoding
       comme processus de création temps réel et performatif
                                      Florine Fouquart, Chu-yin Chen



      To cite this version:
     Florine Fouquart, Chu-yin Chen. Pratique mathématiques de l’art numérique : le shadercoding comme pro-
     cessus de création temps réel et performatif. Arts et Technologies de l’Image, Images numériques et Réalité
     Virtuelle, 2019, 12 (6), pp.527-545. ⟨10.1007/s003710050084⟩. ⟨hal-04421881⟩




                                        HAL Id: hal-04421881
                     https://univ-paris8.hal.science/hal-04421881v1
                                            Submitted on 1 Feb 2024




    HAL is a multi-disciplinary open access archive             L’archive ouverte pluridisciplinaire HAL, est des-
for the deposit and dissemination of scientific re-        tinée au dépôt et à la diffusion de documents scien-
search documents, whether they are published or not.       tifiques de niveau recherche, publiés ou non, émanant
The documents may come from teaching and research          des établissements d’enseignement et de recherche
institutions in France or abroad, or from public or pri-   français ou étrangers, des laboratoires publics ou
vate research centers.                                     privés.


                                              HAL Authorization

Pratique mathématiques de l'art numérique : le shadercoding comme processus
de création temps réel et performatif

                                           Florine Fouquart1, Chu-Yin Chen2
                                          1   Doctorante, Lab. AI-AC, équipe INRéV,
                                                    florine.fouquart@live..fr
                         2   Professeure, Université Paris 8, Dept. Arts et Technologies de l’Image
                                          Directrice de l’équipe INRéV, Lab. AI-AC,
                                                  chu-yin.chen@univ-paris8.fr



                                                           Résumé


Dans un contexte où l'art numérique est de plus en plus présent, il convient de questionner certains de ses aspects,
notamment celui du profil de l'artiste technique. Pour se faire, cet article propose une introduction théorique au
shadercoding, une discipline mêlant programmation, mathématiques et graphisme, mais également une réflexion sur la
performance d'art numérique au travers de cette pratique, dans des événements de programmation en temps-réel.


                                                           Abstract


In the light of digital art being more and more present, raising questions regarding several aspects of it should be done,
especially the question about being a technical artist. To do so, this paper propose a theoretical introduction to
shadercoding, a field where code, mathematics and graphism are blended. Thoughts about performing digital art
through shadercoding in live coding events will also be discussed.


                                                        Introduction


Théorisée dans les années 80 par le chercheur américain John C. Hart, les techniques poussées du shadercoding
employées aujourd'hui sont parties d'une curiosité mathématique : approximer et représenter les fractales, ces formes
complexes issues de formules mathématiques. Ces méthodes permettant d'afficher un très grand nombres d'éléments
dans une image, de façon procédurale et en temps réel, ont fait ensuite une percée discrète dans le domaine de la
production de film d'animation. On peut prendre pour exemple le film Brave des studios Pixar, dans lequel la mousse et
une partie de la petite végétation ont été générées à partir d'une technique de shadercoding appelée le raymarching, mis
en place ici par l'espagnol Inigo Quilez. Aujourd'hui, ces techniques se répandent dans beaucoup de domaines car elles
permettent également de représenter de façon optimisée des objets volumétriques. Par exemple, dans le dernier jeu du
studio Guerrilla Games pour Sony, Horizon Zero Dawn, tous les nuages des paysages sont générés à l'aide du
raymarching.

Un domaine qui lui est resté intouchable pour l'instant, à mon sens, est celui des arts numériques. Il existe des sites en
ligne très accessibles pour pratiquer le shadercoding aisément, des tournois où l’on voit s'affronter deux participants
dans un temps limité ont vu le jour, mais aucune réflexion concernant les possibilités de cette discipline n'a été théorisée
au regard de l'art. Il serait pourtant très intéressant de se pencher sur cette partie de la pratique, qui lie parfaitement la
technique du code, des mathématiques à l'image numérique.

Dans un premier temps, nous reviendrons sur les bases techniques du shadercoding avec une introduction théorique.
Dans un second temps, une analyse d'une pratique performative du shadercoding sera proposée, sous la forme d’un
retour d'expérience.

Présentation théorique et technique du shadercoding


Le shadercoding désigne l'action de coder un shader. Celui-ci est un programme s'adressant directement à la carte
graphique, aussi appelé GPU pour Graphic Processing Unit, de l'ordinateur sur lequel il est exécuté. Il décrit chaque
étape du rendu, c'est-à-dire chaque processus qui vont permettre à la machine d'afficher une image en fonction des
informations des points dans l'espace 3D et de leurs propriétés physiques.

Il existe 4 grands types de shader, représentant chacun une étape du rendu de l'image finale :

    •     Vertex shader > Décrit la position des points dans l'espace 3D

    •     Tessellation shader > Assemble les points en formant des triangles

    •     Geometry shader > Ajoute de nouveaux points et de la définition supplémentaire aux triangles précédents si
          besoin

    •     Fragment (ou pixel) shader > Intervient après la rastérisation1, donne une couleur au pixel en fonction de sa
          position sur la grille de projection




                            Fig 1. Schéma des étapes de rendu d'une image décrite par les shaders qui la composent

Ces programmes sont écrits dans des langages de programmation tels que le GLSL, HLSL, OSL, Metal pour les
produits Apple ou encore en SPIR-V pour les utilisateurs de l'API Vulkan, créée par le consortium Khronos Group.



Ma pratique personnelle du shadercoding s'appuie principalement sur le dernier shader du processus, le fragment
shader. Pour résumer, celui-ci va prendre en entrée la position d'un « point numérique » de l'espace 2D, appelé pixel, et
va retourner une couleur pour le pixel correspondant. C'est donc généralement l'étape utilisée pour coder des post-
process, c'est-à-dire des effets qui vont s'appliquer à posteriori des autres calculs d'objets et de physiques des matériaux.
Il peut s'agir d'un effet de déformation de l'image, d'un effet de contraste, de bloom, etc. Mais la propriété première du
fragment shader peut aussi permettre de générer, à l'aide de formules mathématiques, des motifs ou patterns
particuliers. Ceux-ci peuvent être animés avec des variables évoluant dans le temps ou selon d'autres informations
externes, qui peuvent provenir d'interfaces homme-machine telles qu'un clavier, une souris, une leap motion ou une
kinect, entre autres. Les possibilités génératives sont quasi-infinies, de part la description mathématique d’une image.

Une technique permet même de recréer de la profondeur dans le fragment shader et donc d'afficher à nouveau de la 3D :
le raymarching. Elle a été théorisée la première fois afin de pouvoir représenter en temps réel des formes très complexes
telles que des fractals en 3D de type mandelbulb et des espaces infinis, répétés, contenant un grand nombre de petits
détails. Il s'agit de décrire l'espace selon des fonctions de distances en un point donné, équivalent à nos yeux ou une
caméra filmant la scène par exemple. Ensuite, pour chaque pixel de l'image, on lance un rayon sur lequel on va
'marcher' pas à pas, selon une distance fixe. Chaque rayon va donc, à un moment du parcours de la scène, rencontrer un
objet décrit dans la fonction de distance (appelée communément SDF pour Signed Distance Field).On peut alors

1   Il s'agit de l'étape consistant à projeter les positions des points en 3D sur une grille en deux dimensions afin de constituer l'image finale

afficher ce point de convergence dans l'image.




               Fig 2. Représentation graphique de la technique du Sphere Tracing, optimisation du raymarching - Paniq




Un shader se décrit donc à l'aide de phénomènes physiques et mathématiques parfois complexes, faisant appel aux
matrices et leurs transformées, ou encore aux vecteurs et aux différentes opérations possibles entre eux. Il faut alors
avoir une base de connaissances scientifiques et techniques relativement poussée, si l'on souhaite coder ses propres
shaders. Mais cela en vaut la peine ! La modification de ces programmes à l'aide de formules mathématiques et de
variables animées ouvre des possibilités infinies pour créer, animer et rendre interactif des images numériques en temps
réel.

J'ai donc décidé d'en faire ma pratique artistique tout au long de ma recherche, en utilisant principalement la technique
du raymarching.




                                  Fig 3. Image réalisée en fragment shader sur Shadertoy - Flopine

L'art numérique en temps réel : la performance en shadercoding

Maîtriser l'outil


Comme expliqué précédemment, coder un shader demande de la technicité, des connaissances mathématiques et une
bonne représentation de l'espace, ainsi que des courbes représentant les fonctions les plus utilisées telles que le sinus, la
tangente ou encore le modulo. Celles-ci vont nous permettre de manipuler l'espace en deux ou trois dimensions. On va
pouvoir le tordre, le replier sur lui-même, le symétriser ou le dupliquer à l'infini. Manipuler un shader requiert donc une
certaine aisance mathématique et technique. Il ne s'agit pas non plus de savoir calculer la racine carré de 492 de tête !
Mais plutôt de savoir qu'un produit scalaire entre deux vecteurs orthonormés retourne l'angle entre ces deux vecteurs, ce
qui va nous permettre de représenter le rebond de lumière sur une surface, en faisant le produit scalaire du vecteur
normal au point et de la direction de la source lumineuse.



Cet aspect très technique du shadercoding, que je pratique en tant qu'art, fait résonner en moi la question de la typologie
de l'artiste numérique.

         « Plus qu'une technologie, le numérique est une véritable conception du monde, insufflée par la science qui en
         constitue le soubassement. Ce qui oblige à repenser l'art dans son rapport à la science et à la technique. »
         Edmond Couchot, Norbert Hillaire [1]

Si l'on veut être maître de son œuvre, de la conception à la réalisation jusqu'au produit fini, il ne s'agit plus de
conceptualiser une idée mais bien de maîtriser un processus que l'on peut qualifier de scientifique. Cette idée peut
d'ailleurs être étendue à tout l'art numérique, qui repose sur des technologies de plus en plus avancées et complexes.
Malgré les efforts fait par les concepteurs de matériels et de logiciels pour simplifier l'utilisation de leur produits, une
couche technique sera toujours présente.



         « Le numérique est facteur à la fois de rupture et de continuité. C'est à ce paradoxe que s'affrontent tout ceux
         qui utilisent un ordinateur pour faire œuvre. De la manière dont ils conjuguent le calculable et le sensible, le
         nouveau et le traditionnel, se définit leur esthétique. » Edmond Couchot, Norbert Hillaire [2]

L'artiste numérique veut exprimer une sensation, un vécu, créer du sensible au travers de machines logiques,
réfléchissant à base de 0 et de 1. Une réflexion logique et technique en amont est donc toujours nécessaire pour réaliser
une œuvre numérique. Peut-on alors créer une expérience sensible au travers de l'art numérique, sans perdre une partie
du propos ou du vécu dans les contraintes techniques du numérique ? Pour l'instant cette question reste ouverte.

Pour ma part, avec la pratique du shadercoding, je tente chaque jour de comprendre un peu plus toute la technique et les
mathématiques sous-jacentes à la maîtrise du shader. Connaître et maîtriser le fonctionnement de ces formules
mathématiques dans le contexte de l'écriture d'un shader, va me permettre de les utiliser dans des expérimentations qui
vont alors définir mon esthétique et ma pratique. De part ces connaissances maîtrisées en amont, je peux aujourd'hui
créer instinctivement mes images et même les improviser en temps-réel au moment de l'écriture du code.

Le temps de l’œuvre


         « Puisqu'il est évident que l'inspiration ne forme rien sans matière, il faut donc à l'artiste, à l'origine des arts et
         toujours, quelque premier objet ou quelque première contrainte de fait, sur quoi il exerce d'abord sa
         perception... » Alain [3]

Ces propos d'Alain nous montre une autre voie de la pratique de l'art numérique : les contraintes peuvent être créatrices.
Ce qui nous est imposé peut nous diriger dans notre créativité. La technicité derrière le shadercoding peut donc être
créatrice, elle peut être un moteur de celle-ci. Je trouve cela d'autant plus vrai lorsque l'on rajoute une contrainte de
temps à l'écriture d'un shader, comme cela se fait dans les événements de live coding.

Plus communément appelé Shader Showdown, il s'agit de coder son effet visuel à l'aide d'un shader en 25 ou 30 minutes
devant un public. Suite à cette épreuve, les participants seront jugés par les spectateurs sur différents critères : l'image
finale produite, la technicité du code mais également l'évolution de l'effet au cours de l'épreuve. Ce dernier critère peut
être particulièrement important car, comme son nom l'indique, il est question ici de show, de spectacle à la fois
technique et artistique.



Pour la suite de cet article, je propose de faire un retour d’expérience, une analyse de mon vécu par rapport à cette
discipline et ces événements de live coding.

Mon premier contact avec cet univers fût lors de la Revision Demoparty 2016. Les demoparty sont des rassemblements
de passionnés en informatique et en imagerie numérique, où codeurs et graphistes s’associent pour créer des courts-
métrages sous forme d’exécutable temps-réel, des jeux vidéos ou encore des images dessinées sous Amiga, Commodore
64 ou autres machines anciennes. La Revision est la plus grande demoparty d’Europe et à cette occasion un Shader
Showdown d’envergure y est organisé. Je suis arrivée sur les lieux au moment des qualifications de ce tournoi, le
spectacle était déjà époustouflant. J’ai tout de suite été émerveillée par la complexité des formes, l’écriture du code qui
était tout aussi visible que l’image produite et par l’ambiance électrique devant la scène. Une fois devant cet événement,
j’étais complètement hors de la réalité, hors de l’espace et hors de mon corps. Je pense avoir été proche de l'état que
décrit cette phrase d’Henri Bergson :

         « Ils [les artistes] ne perçoivent plus simplement en vue d'agir ; ils perçoivent pour percevoir, pour rien, pour le
         plaisir. » Henri Bergson [4]



J'ai tout de suite voulu faire partie intégrante de cette discipline, de ce spectacle qui était inédit pour moi. Je me suis
alors plongée dans la pratique, avec comme objectif de comprendre et maîtriser toutes les lignes de code que je tapais.
Ceci dans le but de pouvoir faire émerger mes idées au travers du shadercoding, comme théorisé précédemment.

J'ai écrit des shaders de façon hebdomadaires pendant un an puis quasi-quotidiennement pendant six mois sans jamais
me lasser. À chaque fois, c'était le même bonheur et la même sensation de découverte. Au fur et à mesure que je
maîtrisais la technicité du shadercoding, je pouvais aller plus loin et cela me semblait infini en terme de possibilités.
C'est d'ailleurs toujours le cas aujourd'hui. Tout ce que j'observe m'inspire et je suis constamment en état d'éveil, comme
si une création potentielle était en moi de façon permanente.



En mars 2018, après deux ans de pratiques et de petits tournois amicaux sur Paris, je me suis retrouvée propulsée sur la
même scène devant laquelle je m'étais découverte cette passion pour le shadercoding. J'ai pu participer au Shader
Showdown de la Revision 2018 et aller jusqu'à la finale. Je me suis donc installée sur scène, devant mon écran et surtout
devant plusieurs centaines de personnes qui allaient juger mon travail, trois fois de suite. J'ai commencé à coder et j'ai
ressenti la même chose que lors de ma première rencontre avec cette discipline : j'étais hors du réel, je n'avais plus de
corporalité, je n'étais plus qu'esprit et sensations. J'étais moi-même l'image produite, le code écrit, la performance.
C'était un tout unique. C'était une description de mon esprit, de mon état à un instant T tel un snapshot, un instantané de
ma personnalité. Tout cela était possible aussi car j'avais de la marge pour improviser et être impulsive du fait de ma
maîtrise du langage et de la technicité de cette programmation. J'avais trouvé le moyen technique me correspondant et
me permettant de « faire naître une œuvre », par la communion entre le code (la technique), l'image et l'échange.

         « D'autre part, tout art a pour caractère de faire naître une œuvre et recherche les moyens techniques et
         théoriques de créer une chose appartenant à la catégorie des possibles et dont le principe réside dans la
         personne qui exécute et non dans l’œuvre exécutée. » Aristote [7]



Cet événement a été décisif dans la direction de ma recherche et de ma pratique. Je peux affirmer aujourd'hui qu'il est
possible de faire des performances artistiques avec du code et du shadercoding. J'ai été actrice d'une performance
numérique et évolutive, en interaction forte avec de nombreux spectateurs.

           « La volonté de faire participer peu ou prou , à travers un dialogue le plus souvent plurisensoriel, le spectateur
           à l'élaboration de l’œuvre change en profondeur les rapports traditionnels entre l'auteur, l’œuvre et le
           spectateur. » Edmond Couchot, Norbert Hillaire [5]



Il serait intéressant de se pencher sur la temporalité qui englobe cette performance. Du point de vue de l'artiste, le temps
de la conception est le même que celui de la création qui est le temps-réel, à la fois au sens du temps présent et de la
particularité des images qui sont à opposer à celles dites pré-calculées. Il s'agit du temps du code saisi. Du point de vue
du spectateur, c'est le temps de l'image produite, le temps de la programmation et celui de la réception de l’œuvre.
S'instaure alors un dialogue artiste – spectateur, que je souhaite explorer plus en profondeur au fur et à mesure de mes
différentes performances, toujours avec le shadercoding et cette notion de live coding, de programmation en directe et
visible, que je compte bien pratiquer des années encore !

           « L'art doit chaque jour retourner à rien pour chaque jour commencer. L'art est quelque chose qui naît »
           Michel Seuphor [6]




                Fig 4. Shader réalisé en raymarching lors des qualifications du Shader Showdown de la Revision 2018 - Flopine




Références
[1] Couchot, E. and Hillaire, N. L’art numérique : comment la technologie vient au monde de l’art. Flammarion, 2003.

[2] Ibid

[3] Alain Le système des beaux arts. 1920.

[4] Bergson H. La pensée et le mouvant. P.U.F. 1966.

[5] Couchot, E. and Hillaire, N. L’art numérique : comment la technologie vient au monde de l’art. Flammarion, 2003.

[6] Seuphor M. Le style et le cri. Le Seuil. 1965.

[7] Aristote. Éthique à Nicomaque, VI. Garnier-Flammarion. 1965.
