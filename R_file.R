#!/usr/bin/env Rscript
suppressPackageStartupMessages(require(workflowscriptscommon))
suppressPackageStartupMessages(require(utils))
suppressPackageStartupMessages(require(Seurat))
suppressPackageStartupMessages(require(future))
suppressPackageStartupMessages(require(pbapply))
suppressPackageStartupMessages(require(optparse))
suppressPackageStartupMessages(require(RANN))

option_list <- list(
    make_option(
                    c('--format'),
                    action='store',
                    default='seurat',
                    metavar='Input format',
                    type='character',
                    help='Either loom, seurat, anndata or singlecellexperiment for the input format to read.')
,
    make_option(
                    c('-i','--input_path'),
                    action='store',
                    metavar='Input file',
                    type='character',
                    help='Input file with Seurat object in either RDS-Seurat, Loom or SCE')
,
    make_option(
                    c('--reference.assay'),
                    action='store',
                    default=NULL,
                    type='character',
                    help='reference.assay Assay to use from reference')
,
    make_option(
                    c('--query.assay'),
                    action='store',
                    default=NULL,
                    type='character',
                    help='query.assay Assay to use from query')
,
    make_option(
                    c('--reduction'),
                    action='store',
                    default='pcaproject',
                    type='character',
                    help='reduction Dimensional reduction to perform when finding anchors. Options are: itemize    itempcaproject: Project the PCA from the reference onto the query. We recommend using PCA    when reference and query datasets are from scRNA-seq    itemcca: Run a CCA on the reference and query  ')
,
    make_option(
                    c('--normalization-method'),
                    action='store',
                    default='SCT',
                    type='character',
                    help='blablabla')
,
    make_option(
                    c('--project.query'),
                    action='store_true',
                    default=FALSE,
                    type='logical',
                    help='project.query Project the PCA from the query dataset onto the reference. Use only in rare cases where the query dataset has a much larger cell number, but the reference dataset has a unique assay for transfer.')
,
    make_option(
                    c('--features'),
                    action='store',
                    default=NULL,
                    type='character',
                    help='features Features to use for dimensional reduction')
,
    make_option(
                    c('--npcs'),
                    action='store',
                    default='30',
                    type='character',
                    help='npcs Number of PCs to compute on reference. If null, then use an existing PCA structure in the reference object')
,
    make_option(
                    c('--do-not-l2.norm'),
                    action='store_false',
                    default=TRUE,
                    type='logical',
                    help='l2.norm Perform L2 normalization on the cell embeddings after dimensional reduction')
,
    make_option(
                    c('--k.anchor'),
                    action='store',
                    default='5',
                    type='character',
                    help='k.anchor How many neighbors (k) to use when picking anchors')
,
    make_option(
                    c('--k.filter'),
                    action='store',
                    default='200',
                    type='character',
                    help='k.filter How many neighbors (k) to use when filtering anchors')
,
    make_option(
                    c('--k.score'),
                    action='store',
                    default='30',
                    type='character',
                    help='k.score How many neighbors (k) to use when scoring anchors')
,
    make_option(
                    c('--max.features'),
                    action='store',
                    default='200',
                    type='character',
                    help='max.features The maximum number of features to use when specifying the neighborhood search space in the anchor filtering')
,
    make_option(
                    c('--nn.method'),
                    action='store',
                    default='rann',
                    type='character',
                    help='nn.method Method for nearest neighbor finding. Options include: rann, annoy')
,
    make_option(
                    c('--eps'),
                    action='store',
                    default='0',
                    type='character',
                    help='eps Error bound on the neighbor finding algorithm (from RANN)')
,
    make_option(
                    c('--do-not-approx.pca'),
                    action='store_false',
                    default=TRUE,
                    type='logical',
                    help='approx.pca Use truncated singular value decomposition to approximate PCA')
,
    make_option(
                    c('--do-not-verbose'),
                    action='store_false',
                    default=TRUE,
                    type='logical',
                    help='verbose Print progress bars and output')
)

opt <- wsc_parse_args(option_list, 
                      mandatory = c('input_path'))


dims <- wsc_parse_numeric(opt, dims)





if ( ! file.exists(opt$input_path) ) {
    stop((paste('File', opt$input_path, 'does not exist')))
}



if ( ! file.exists(opt$input_path) ) {
    stop((paste('File', opt$input_path, 'does not exist')))
}


reference <- read_seurat3_object(input_path = opt$input_path,
                    format = opt$format)

query <- read_seurat3_object(input_path = opt$input_path,
                    format = opt$format)

anchor_object <- FindTransferAnchors(reference = reference,
                    query = query,
                    reference.assay = opt$reference.assay,
                    query.assay = opt$query.assay,
                    reduction = opt$reduction,
                    normalization.method = opt$normalization_method,
                    project.query = opt$project.query,
                    features = opt$features,
                    npcs = opt$npcs,
                    l2.norm = !opt$do_not_l2.norm,
                    k.anchor = opt$k.anchor,
                    k.filter = opt$k.filter,
                    dims = dims,
                    k.score = opt$k.score,
                    max.features = opt$max.features,
                    nn.method = opt$nn.method,
                    eps = opt$eps,
                    approx.pca = !opt$do_not_approx.pca,
                    verbose = !opt$do_not_verbose)



saveRDS(anchor_object)

