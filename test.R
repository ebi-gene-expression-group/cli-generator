#' @include generics.R
#'
NULL

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Functions
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#' Find integration anchors
#'
#' Finds the integration anchors
#'
#' @param object.list A list of objects between which to find anchors for
#' downstream integration.
#' @param assay A vector of assay names specifying which assay to use when
#' constructing anchors. If NULL, the current default assay for each object is
#' used.
#' @param reference A vector specifying the object/s to be used as a reference
#' during integration. If NULL (default), all pairwise anchors are found (no
#' reference/s). If not NULL, the corresponding objects in \code{object.list}
#' will be used as references. When using a set of specified references, anchors
#' are first found between each query and each reference. The references are
#' then integrated through pairwise integration. Each query is then mapped to
#' the integrated reference.
#' @param anchor.features Can be either:
#' \itemize{
#'   \item{A numeric value. This will call \code{\link{SelectIntegrationFeatures}}
#'   to select the provided number of features to be used in anchor finding}
#'   \item{A vector of features to be used as input to the anchor finding process}
#' }
#' @param scale Whether or not to scale the features provided. Only set to FALSE
#' if you have previously scaled the features you want to use for each object in
#' the object.list
#' @param normalization.method Name of normalization method used: LogNormalize
#' or SCT
#' @param sct.clip.range Numeric of length two specifying the min and max values
#' the Pearson residual will be clipped to
#' @param reduction Dimensional reduction to perform when finding anchors. Can
#' be one of:
#' \itemize{
#'   \item{cca: Canonical correlation analysis}
#'   \item{rpca: Reciprocal PCA}
#' }
#' @param l2.norm Perform L2 normalization on the CCA cell embeddings after
#' dimensional reduction
#' @param dims Which dimensions to use from the CCA to specify the neighbor
#' search space
#' @param k.anchor How many neighbors (k) to use when picking anchors
#' @param k.filter How many neighbors (k) to use when filtering anchors
#' @param k.score How many neighbors (k) to use when scoring anchors
#' @param max.features The maximum number of features to use when specifying the
#' neighborhood search space in the anchor filtering
#' @param nn.method Method for nearest neighbor finding. Options include: rann,
#' annoy
#' @param eps Error bound on the neighbor finding algorithm (from RANN)
#' @param verbose Print progress bars and output
#'
#' @return Returns an AnchorSet object
#'
#' @importFrom pbapply pblapply
#' @importFrom future.apply future_lapply
#' @importFrom future nbrOfWorkers
#'
#' @export
#'
FindIntegrationAnchors <- function(
  object.list = NULL,
  assay = NULL,
  reference = NULL,
  anchor.features = 2000,
  scale = TRUE,
  normalization.method = c("LogNormalize", "SCT"),
  sct.clip.range = NULL,
  reduction = c("cca", "rpca"),
  l2.norm = TRUE,
  dims = 1:30,
  k.anchor = 5,
  k.filter = 200,
  k.score = 30,
  max.features = 200,
  nn.method = "rann",
  eps = 0,
  verbose = TRUE
) {
  normalization.method <- match.arg(arg = normalization.method)
  reduction <- match.arg(arg = reduction)
  if (reduction == "rpca") {
    reduction <- "pca"
  }
  my.lapply <- ifelse(
    test = verbose && nbrOfWorkers() == 1,
    yes = pblapply,
    no = future_lapply
  )
  object.ncells <- sapply(X = object.list, FUN = function(x) dim(x = x)[2])
  if (any(object.ncells <= max(dims))) {
    bad.obs <- which(x = object.ncells <= max(dims))
    stop("Max dimension too large: objects ", paste(bad.obs, collapse = ", "),
         " contain fewer than ", max(dims), " cells. \n Please specify a",
         " maximum dimensions that is less than the number of cells in any ",
         "object (", min(object.ncells), ").")
  }
  if (!is.null(x = assay)) {
    if (length(x = assay) != length(x = object.list)) {
      stop("If specifying the assay, please specify one assay per object in the object.list")
    }
    object.list <- sapply(
      X = 1:length(x = object.list),
      FUN = function(x) {
        DefaultAssay(object = object.list[[x]]) <- assay[x]
        return(object.list[[x]])
      }
    )
  } else {
    assay <- sapply(X = object.list, FUN = DefaultAssay)
  }
  object.list <- CheckDuplicateCellNames(object.list = object.list)

  slot <- "data"
  if (normalization.method == "SCT") {
    slot <- "scale.data"
    scale <- FALSE
    if (is.numeric(x = anchor.features)) {
      stop("Please specify the anchor.features to be used. The expected ",
      "workflow for integratinge assays produced by SCTransform is ",
      "SelectIntegrationFeatures -> PrepSCTIntegration -> ",
      "FindIntegrationAnchors.")
    }
    sct.check <- sapply(
      X = 1:length(x = object.list),
      FUN = function(x) {
        sct.cmd <- grep(
          pattern = 'PrepSCTIntegration',
          x = Command(object = object.list[[x]]),
          value = TRUE
        )
        # check assay has gone through PrepSCTIntegration
        if (!any(grepl(pattern = "PrepSCTIntegration", x = Command(object = object.list[[x]]))) ||
            Command(object = object.list[[x]], command = sct.cmd, value = "assay") != assay[x]) {
          stop("Object ", x, " assay - ", assay[x], " has not been processed ",
          "by PrepSCTIntegration. Please run PrepSCTIntegration prior to ",
          "FindIntegrationAnchors if using assays generated by SCTransform.", call. = FALSE)
        }
        # check that the correct features are being used
        if (all(Command(object = object.list[[x]], command = sct.cmd, value = "anchor.features") != anchor.features)) {
          stop("Object ", x, " assay - ", assay[x], " was processed using a ",
          "different feature set than in PrepSCTIntegration. Please rerun ",
          "PrepSCTIntegration with the same anchor.features for all objects in ",
          "the object.list.", call. = FALSE)
        }
      }
    )
  }
  if (is.numeric(x = anchor.features) && normalization.method != "SCT") {
    if (verbose) {
      message("Computing ", anchor.features, " integration features")
    }
    anchor.features <- SelectIntegrationFeatures(
      object.list = object.list,
      nfeatures = anchor.features,
      assay = assay
    )
  }
  if (scale) {
    if (verbose) {
      message("Scaling features for provided objects")
    }
    object.list <- my.lapply(
      X = object.list,
      FUN = function(object) {
        ScaleData(object = object, features = anchor.features, verbose = FALSE)
      }
    )
  }
  nn.reduction <- reduction
  # if using pca, only need to compute the internal neighborhood structure once
  # for each dataset
  internal.neighbors <- list()
  if (nn.reduction == "pca") {
    k.filter <- NA
    if (verbose) {
      message("Computing within dataset neighborhoods")
    }
    k.neighbor <- max(k.anchor, k.score)
    internal.neighbors <- my.lapply(
      X = 1:length(x = object.list),
      FUN = function(x) {
        NNHelper(
          data = Embeddings(object = object.list[[x]][[nn.reduction]])[, dims],
          k = k.neighbor + 1,
          method = nn.method,
          eps = eps
        )
      }
    )
  }
  # determine pairwise combinations
  combinations <- expand.grid(1:length(x = object.list), 1:length(x = object.list))
  combinations <- combinations[combinations$Var1 < combinations$Var2, , drop = FALSE]
  # determine the proper offsets for indexing anchors
  objects.ncell <- sapply(X = object.list, FUN = ncol)
  offsets <- as.vector(x = cumsum(x = c(0, objects.ncell)))[1:length(x = object.list)]
  if (is.null(x = reference)) {
    # case for all pairwise, leave the combinations matrix the same
    if (verbose) {
      message("Finding all pairwise anchors")
    }
  } else {
    reference <- unique(x = sort(x = reference))
    if (max(reference) > length(x = object.list)) {
      stop('Error: requested reference object ', max(reference), " but only ",
           length(x = object.list), " objects provided")
    }
    # modify the combinations matrix to retain only R-R and R-Q comparisons
    if (verbose) {
      message("Finding anchors between all query and reference datasets")
      ok.rows <- (combinations$Var1 %in% reference) | (combinations$Var2 %in% reference)
      combinations <- combinations[ok.rows, ]
    }
  }
  # determine all anchors
  all.anchors <- my.lapply(
    X = 1:nrow(x = combinations),
    FUN = function(row) {
      i <- combinations[row, 1]
      j <- combinations[row, 2]
      object.1 <- DietSeurat(
        object = object.list[[i]],
        assays = assay[i],
        features = anchor.features,
        counts = FALSE,
        scale.data = TRUE,
        dimreducs = reduction
      )
      object.2 <- DietSeurat(
        object = object.list[[j]],
        assays = assay[j],
        features = anchor.features,
        counts = FALSE,
        scale.data = TRUE,
        dimreducs = reduction
      )
      # suppress key duplication warning
      suppressWarnings(object.1[["ToIntegrate"]] <- object.1[[assay[i]]])
      DefaultAssay(object = object.1) <- "ToIntegrate"
      if (reduction %in% Reductions(object = object.1)) {
        slot(object = object.1[[reduction]], name = "assay.used") <- "ToIntegrate"
      }
      object.1 <- DietSeurat(object = object.1, assays = "ToIntegrate", scale.data = TRUE, dimreducs = reduction)
      suppressWarnings(object.2[["ToIntegrate"]] <- object.2[[assay[j]]])
      DefaultAssay(object = object.2) <- "ToIntegrate"
      if (reduction %in% Reductions(object = object.2)) {
        slot(object = object.2[[reduction]], name = "assay.used") <- "ToIntegrate"
      }
      object.2 <- DietSeurat(object = object.2, assays = "ToIntegrate", scale.data = TRUE, dimreducs = reduction)
      object.pair <- switch(
        EXPR = reduction,
        'cca' = {
          object.pair <- RunCCA(
            object1 = object.1,
            object2 = object.2,
            assay1 = "ToIntegrate",
            assay2 = "ToIntegrate",
            features = anchor.features,
            num.cc = max(dims),
            renormalize = FALSE,
            rescale = FALSE,
            verbose = verbose
          )
          if (l2.norm){
            object.pair <- L2Dim(object = object.pair, reduction = reduction)
            reduction <- paste0(reduction, ".l2")
            nn.reduction <- reduction
          }
          reduction.2 <- character()
          object.pair
        },
        'pca' = {
          common.features <- intersect(
            x = rownames(x = Loadings(object = object.1[["pca"]])),
            y = rownames(x = Loadings(object = object.2[["pca"]]))
          )
          object.pair <- merge(x = object.1, y = object.2, merge.data = TRUE)
          projected.embeddings.1<- t(x = GetAssayData(object = object.1, slot = "scale.data")[common.features, ]) %*%
            Loadings(object = object.2[["pca"]])[common.features, ]
          object.pair[['projectedpca.1']] <- CreateDimReducObject(
            embeddings = rbind(projected.embeddings.1, Embeddings(object = object.2[["pca"]])),
            assay = DefaultAssay(object = object.1),
            key = "projectedpca1_"
          )
          projected.embeddings.2 <- t(x = GetAssayData(object = object.2, slot = "scale.data")[common.features, ]) %*%
            Loadings(object = object.1[["pca"]])[common.features, ]
          object.pair[['projectedpca.2']] <- CreateDimReducObject(
            embeddings = rbind(projected.embeddings.2, Embeddings(object = object.1[["pca"]])),
            assay = DefaultAssay(object = object.2),
            key = "projectedpca2_"
          )
          object.pair[["pca"]] <- CreateDimReducObject(
            embeddings = rbind(
              Embeddings(object = object.1[["pca"]]),
              Embeddings(object = object.2[["pca"]])),
            assay = DefaultAssay(object = object.1),
            key = "pca_"
          )
          reduction <- "projectedpca.1"
          reduction.2 <- "projectedpca.2"
          if (l2.norm){
            slot(object = object.pair[["projectedpca.1"]], name = "cell.embeddings") <- Sweep(
              x = Embeddings(object = object.pair[["projectedpca.1"]]),
              MARGIN = 2,
              STATS = apply(X = Embeddings(object = object.pair[["projectedpca.1"]]), MARGIN = 2, FUN = sd),
              FUN = "/"
            )
            slot(object = object.pair[["projectedpca.2"]], name = "cell.embeddings") <- Sweep(
              x = Embeddings(object = object.pair[["projectedpca.2"]]),
              MARGIN = 2,
              STATS = apply(X = Embeddings(object = object.pair[["projectedpca.2"]]), MARGIN = 2, FUN = sd),
              FUN = "/"
            )
            object.pair <- L2Dim(object = object.pair, reduction = "projectedpca.1")
            object.pair <- L2Dim(object = object.pair, reduction = "projectedpca.2")
            reduction <- paste0(reduction, ".l2")
            reduction.2 <- paste0(reduction.2, ".l2")
          }
          object.pair
        },
        stop("Invalid reduction parameter. Please choose either cca or rpca")
      )
      internal.neighbors <- internal.neighbors[c(i, j)]
      anchors <- FindAnchors(
        object.pair = object.pair,
        assay = c("ToIntegrate", "ToIntegrate"),
        slot = slot,
        cells1 = colnames(x = object.1),
        cells2 = colnames(x = object.2),
        internal.neighbors = internal.neighbors,
        reduction = reduction,
        reduction.2 = reduction.2,
        nn.reduction = nn.reduction,
        dims = dims,
        k.anchor = k.anchor,
        k.filter = k.filter,
        k.score = k.score,
        max.features = max.features,
        nn.method = nn.method,
        eps = eps,
        verbose = verbose
      )
      anchors[, 1] <- anchors[, 1] + offsets[i]
      anchors[, 2] <- anchors[, 2] + offsets[j]
      return(anchors)
    }
  )
  all.anchors <- do.call(what = 'rbind', args = all.anchors)
  all.anchors <- rbind(all.anchors, all.anchors[, c(2, 1, 3)])
  all.anchors <- AddDatasetID(anchor.df = all.anchors, offsets = offsets, obj.lengths = objects.ncell)
  command <- LogSeuratCommand(object = object.list[[1]], return.command = TRUE)
  anchor.set <- new(Class = "AnchorSet",
                    object.list = object.list,
                    reference.objects = reference %||% seq_along(object.list),
                    anchors = all.anchors,
                    offsets = offsets,
                    anchor.features = anchor.features,
                    command = command
  )
  return(anchor.set)
}

#' Find transfer anchors
#'
#' Finds the transfer anchors
#'
#' @param reference Seurat object to use as the reference
#' @param query Seurat object to use as the query
#' @param reference.assay Assay to use from reference
#' @param query.assay Assay to use from query
#' @param reduction Dimensional reduction to perform when finding anchors. Options are:
#' \itemize{
#'    \item{pcaproject: Project the PCA from the reference onto the query. We recommend using PCA
#'    when reference and query datasets are from scRNA-seq}
#'    \item{cca: Run a CCA on the reference and query }
#' }
#' @param project.query Project the PCA from the query dataset onto the reference. Use only in rare
#' cases where the query dataset has a much larger cell number, but the reference dataset has a
#' unique assay for transfer.
#' @param features Features to use for dimensional reduction
#' @param normalization.method Name of normalization method used: LogNormalize or SCT
#' @param npcs Number of PCs to compute on reference. If null, then use an existing PCA structure in
#' the reference object
#' @param l2.norm Perform L2 normalization on the cell embeddings after dimensional reduction
#' @param dims Which dimensions to use from the reduction to specify the neighbor search space
#' @param k.anchor How many neighbors (k) to use when picking anchors
#' @param k.filter How many neighbors (k) to use when filtering anchors
#' @param k.score How many neighbors (k) to use when scoring anchors
#' @param max.features The maximum number of features to use when specifying the neighborhood search
#' space in the anchor filtering
#'@param nn.method Method for nearest neighbor finding. Options include: rann,
#' annoy
#' @param eps Error bound on the neighbor finding algorithm (from RANN)
#' @param approx.pca Use truncated singular value decomposition to approximate PCA
#' @param verbose Print progress bars and output
#'
#' @return Returns an AnchorSet object
#'
#'
#' @export
#'
FindTransferAnchors <- function(
  reference,
  query,
  normalization.method = c("LogNormalize", "SCT"),
  reference.assay = NULL,
  query.assay = NULL,
  reduction = "pcaproject",
  project.query = FALSE,
  features = NULL,
  npcs = 30,
  l2.norm = TRUE,
  dims = 1:30,
  k.anchor = 5,
  k.filter = 200,
  k.score = 30,
  max.features = 200,
  nn.method = "rann",
  eps = 0,
  approx.pca = TRUE,
  verbose = TRUE
) {
  if (length(x = reference) > 1 | length(x = query) > 1) {
    stop("We currently only support transfer between a single query and reference")
  }
  if (!reduction %in% c("pcaproject", "cca", "pcaqueryproject")) {
    stop("Please select either pcaproject, cca, or pcaqueryproject for the reduction parameter.")
  }
  if (reduction %in% c('pcaproject', 'pcaqueryproject')) {
    projected = TRUE
  } else {
    projected = FALSE
  }
  normalization.method <- match.arg(arg = normalization.method)
  query <- RenameCells(
    object = query,
    new.names = paste0(Cells(x = query), "_", "query")
  )
  reference <- RenameCells(
    object = reference,
    new.names = paste0(Cells(x = reference), "_", "reference")
  )
  features <- features %||% VariableFeatures(object = reference)
  reference.assay <- reference.assay %||% DefaultAssay(object = reference)
  query.assay <- query.assay %||% DefaultAssay(object = query)
  DefaultAssay(object = reference) <- reference.assay
  DefaultAssay(object = query) <- query.assay
  feature.mean <- NULL
  slot <- "data"
  if (normalization.method == "SCT") {
    features <- intersect(x = features, y = rownames(x = query))
    query <- GetResidual(object = query, features = features, verbose = FALSE)
    query[[query.assay]] <- CreateAssayObject(
      counts =  as.sparse(x = GetAssayData(object = query[[query.assay]], slot = "scale.data")[features, ])
    )
    query <- SetAssayData(
      object = query,
      slot = "data",
      assay = query.assay,
      new.data = GetAssayData(object = query[[query.assay]], slot = "counts")
    )
    query <- SetAssayData(
      object = query,
      slot = "scale.data",
      assay = query.assay,
      new.data = as.matrix(x = GetAssayData(object = query[[query.assay]], slot = "counts"))
    )
    if (IsSCT(assay = reference[[reference.assay]])) {
      reference <- GetResidual(object = reference, features = features, verbose = FALSE)
    }
    reference[[reference.assay]] <- CreateAssayObject(
      counts =  as.sparse(x = GetAssayData(object = reference[[reference.assay]], slot = "scale.data")[features, ])
    )
    reference <- SetAssayData(
      object = reference,
      slot = "data",
      assay = reference.assay,
      new.data = GetAssayData(object = reference[[reference.assay]], slot = "counts")
    )
    reference <- SetAssayData(
      object = reference,
      slot = "scale.data",
      assay = reference.assay,
      new.data =  as.matrix(x = GetAssayData(object = reference[[reference.assay]], slot = "counts"))
    )
    feature.mean <- "SCT"
    slot <- "scale.data"
  }
  ## find anchors using PCA projection
  if (reduction == 'pcaproject') {
    if (project.query) {
      if (!is.null(x = npcs)) {
        if (verbose) {
          message("Performing PCA on the provided query using ", length(x = features), " features as input.")
        }
        if (normalization.method == "LogNormalize") {
          query <- ScaleData(object = query, features = features, verbose = FALSE)
        }
        query <- RunPCA(object = query, npcs = npcs, verbose = FALSE, features = features, approx = approx.pca)
      }
      projected.pca <- ProjectCellEmbeddings(
        reference = query,
        query = reference,
        dims = dims,
        verbose = verbose
      )
      query.pca <- Embeddings(object = query[["pca"]])[, dims]
      combined.pca <- CreateDimReducObject(
        embeddings = as.matrix(x = rbind(projected.pca,query.pca))[, dims],
        key = "ProjectPC_",
        assay = reference.assay
      )
      combined.ob <- merge(x = reference, y = query)
      combined.ob[["pcaproject"]] <- combined.pca
      old.loadings <- Loadings(object = query[["pca"]])
      colnames(x = old.loadings) <- paste0("ProjectPC_", 1:ncol(x = old.loadings))
      Loadings(object = combined.ob[["pcaproject"]]) <- old.loadings[, dims]
    } else {
      if (!is.null(x = npcs)) {
        if (verbose) {
          message("Performing PCA on the provided reference using ", length(x = features), " features as input.")
        }
        if (normalization.method == "LogNormalize") {
          reference <- ScaleData(object = reference, features = features, verbose = FALSE)
        }
        reference <- RunPCA(
          object = reference,
          npcs = npcs,
          verbose = FALSE,
          features = features,
          approx = approx.pca
        )
      }
      projected.pca <- ProjectCellEmbeddings(
        reference = reference,
        query = query,
        dims = dims,
        feature.mean = feature.mean,
        verbose = verbose
      )
      ref.pca <- Embeddings(object = reference[["pca"]])[, dims]
      combined.pca <- CreateDimReducObject(
        embeddings = as.matrix(x = rbind(ref.pca, projected.pca))[, dims],
        key = "ProjectPC_",
        assay = reference.assay
      )
      combined.ob <- merge(x = reference, y = query)
      combined.ob[["pcaproject"]] <- combined.pca
      old.loadings <- Loadings(object = reference[["pca"]])
      colnames(x = old.loadings) <- paste0("ProjectPC_", 1:ncol(x = old.loadings))
      Loadings(object = combined.ob[["pcaproject"]]) <- old.loadings[, dims]
    }
  }
  ## find anchors using CCA
  if (reduction == 'cca') {
    if (normalization.method == "LogNormalize") {
      reference <- ScaleData(object = reference, features = features, verbose = FALSE)
      query <- ScaleData(object = query, features = features, verbose = FALSE)
    }
    combined.ob <- RunCCA(
      object1 = reference,
      object2 = query,
      features = features,
      num.cc = max(dims),
      renormalize = FALSE,
      rescale = FALSE,
      verbose = verbose
    )
  }
  if (l2.norm) {
    combined.ob <- L2Dim(object = combined.ob, reduction = reduction)
    reduction <- paste0(reduction, ".l2")
  }
  slot <- "data"
  anchors <- FindAnchors(
    object.pair = combined.ob,
    assay = c(reference.assay, query.assay),
    slot = slot,
    cells1 = colnames(x = reference),
    cells2 = colnames(x = query),
    reduction = reduction,
    internal.neighbors = list(NULL, NULL),
    dims = dims,
    k.anchor = k.anchor,
    k.filter = k.filter,
    k.score = k.score,
    max.features = max.features,
    nn.method = nn.method,
    eps = eps,
    projected = projected,
    verbose = verbose
  )
  command <- LogSeuratCommand(object = combined.ob, return.command = TRUE)
  anchor.set <- new(
    Class = "AnchorSet",
    object.list = list(combined.ob),
    reference.cells = colnames(x = reference),
    query.cells = colnames(x = query),
    anchors = anchors,
    anchor.features = features,
    command = command
  )
  return(anchor.set)
}

#' Integrate data
#'
#' Perform dataset integration using a pre-computed anchorset
#'
#' @param anchorset Results from FindIntegrationAnchors
#' @param new.assay.name Name for the new assay containing the integrated data
#' @param normalization.method Name of normalization method used: LogNormalize
#' or SCT
#' @param features Vector of features to use when computing the PCA to determine the weights. Only set
#' if you want a different set from those used in the anchor finding process
#' @param features.to.integrate Vector of features to integrate. By default, will use the features
#' used in anchor finding.
#' @param dims Number of PCs to use in the weighting procedure
#' @param k.weight Number of neighbors to consider when weighting
#' @param weight.reduction Dimension reduction to use when calculating anchor weights.
#' This can be either:
#' \itemize{
#'    \item{A string, specifying the name of a dimension reduction present in all objects to be integrated}
#'    \item{A vector of strings, specifying the name of a dimension reduction to use for each object to be integrated}
#'    \item{A vector of Dimreduc objects, specifying the object to use for each object in the integration}
#'    \item{NULL, in which case a new PCA will be calculated and used to calculate anchor weights}
#' }
#' Note that, if specified, the requested dimension reduction will only be used for calculating anchor weights in the
#' first merge between reference and query, as the merged object will subsequently contain more cells than was in
#' query, and weights will need to be calculated for all cells in the object.
#' @param sd.weight Controls the bandwidth of the Gaussian kernel for weighting
#' @param sample.tree Specify the order of integration. If NULL, will compute automatically.
#' @param preserve.order Do not reorder objects based on size for each pairwise integration.
#' @param do.cpp Run cpp code where applicable
#' @param eps Error bound on the neighbor finding algorithm (from \code{\link{RANN}})
#' @param verbose Print progress bars and output
#'
#' @return Returns a Seurat object with a new integrated Assay
#'
#' @export
#'
IntegrateData <- function(
  anchorset,
  new.assay.name = "integrated",
  normalization.method = c("LogNormalize", "SCT"),
  features = NULL,
  features.to.integrate = NULL,
  dims = 1:30,
  k.weight = 100,
  weight.reduction = NULL,
  sd.weight = 1,
  sample.tree = NULL,
  preserve.order = FALSE,
  do.cpp = TRUE,
  eps = 0,
  verbose = TRUE
) {
  normalization.method <- match.arg(arg = normalization.method)
  reference.datasets <- slot(object = anchorset, name = 'reference.objects')
  object.list <- slot(object = anchorset, name = 'object.list')
  anchors <- slot(object = anchorset, name = 'anchors')
  ref <- object.list[reference.datasets]
  features <- features %||% slot(object = anchorset, name = "anchor.features")
  unintegrated <- merge(
    x = object.list[[1]],
    y = object.list[2:length(x = object.list)]
  )
  if (normalization.method == "SCT") {
    vst.set <- list()
    for (i in 1:length(x = object.list)) {
      assay <- DefaultAssay(object = object.list[[i]])
      object.list[[i]][[assay]] <- CreateAssayObject(
        data = GetAssayData(object = object.list[[i]], assay = assay, slot = "scale.data")
      )
    }
    slot(object = anchorset, name = "object.list") <- object.list
  }
  # perform pairwise integration of reference objects
  reference.integrated <- PairwiseIntegrateReference(
    anchorset = anchorset,
    new.assay.name = new.assay.name,
    normalization.method = normalization.method,
    features = features,
    features.to.integrate = features.to.integrate,
    dims = dims,
    k.weight = k.weight,
    weight.reduction = weight.reduction,
    sd.weight = sd.weight,
    sample.tree = sample.tree,
    preserve.order = preserve.order,
    do.cpp = do.cpp,
    eps = eps,
    verbose = verbose
  )
  if (length(x = reference.datasets) == length(x = object.list)) {
    if (normalization.method == "SCT") {
      reference.integrated <- SetAssayData(
        object = reference.integrated,
        assay = new.assay.name,
        slot = "scale.data",
        new.data = ScaleData(
          object = GetAssayData(object = reference.integrated, assay = new.assay.name, slot = "scale.data"),
          do.scale = FALSE,
          do.center = TRUE,
          verbose = FALSE
        )
      )
      reference.integrated[[assay]] <- unintegrated[[assay]]
    }
    return(reference.integrated)
  } else {
    active.assay <- DefaultAssay(object = ref[[1]])
    reference.integrated[[active.assay]] <- NULL
    reference.integrated[[active.assay]] <- CreateAssayObject(
      data = GetAssayData(
        object = reference.integrated[[new.assay.name]],
        slot = 'data'
      )
    )
    DefaultAssay(object = reference.integrated) <- active.assay
    reference.integrated[[new.assay.name]] <- NULL
    VariableFeatures(object = reference.integrated) <- features
    # Extract the query objects (if any) and map to reference
    integrated.data <- MapQuery(
      anchorset = anchorset,
      reference = reference.integrated,
      new.assay.name = new.assay.name,
      normalization.method = normalization.method,
      features = features,
      features.to.integrate = features.to.integrate,
      dims = dims,
      k.weight = k.weight,
      weight.reduction = weight.reduction,
      sd.weight = sd.weight,
      sample.tree = sample.tree,
      preserve.order = preserve.order,
      do.cpp = do.cpp,
      eps = eps,
      verbose = verbose
    )

    # Construct final assay object
    integrated.assay <- CreateAssayObject(
      data = integrated.data
    )
    if (normalization.method == "SCT") {
      integrated.assay <- SetAssayData(
        object = integrated.assay,
        slot = "scale.data",
        new.data =  ScaleData(
          object = GetAssayData(object = integrated.assay, slot = "data"),
          do.scale = FALSE,
          do.center = TRUE,
          verbose = FALSE
        )
      )
      integrated.assay <- SetAssayData(
        object = integrated.assay,
        slot = "data",
        new.data = GetAssayData(object = integrated.assay, slot = "scale.data")
      )
    }
    unintegrated[[new.assay.name]] <- integrated.assay
    unintegrated <- SetIntegrationData(
      object = unintegrated,
      integration.name = "Integration",
      slot = "anchors",
      new.data = anchors
    )
    DefaultAssay(object = unintegrated) <- new.assay.name
    VariableFeatures(object = unintegrated) <- features
    unintegrated[["FindIntegrationAnchors"]] <- slot(object = anchorset, name = "command")
    unintegrated <- LogSeuratCommand(object = unintegrated)
    return(unintegrated)
  }
}

#' Calculate the local structure preservation metric
#'
#' Calculates a metric that describes how well the local structure of each group
#' prior to integration is preserved after integration. This procedure works as
#' follows: For each group, compute a PCA, compute the top num.neighbors in pca
#' space, compute the top num.neighbors in corrected pca space, compute the
#' size of the intersection of those two sets of neighbors.
#' Return the average over all groups.
#'
#' @param object Seurat object
#' @param grouping.var Grouping variable
#' @param idents Optionally specify a set of idents to compute metric for
#' @param neighbors Number of neighbors to compute in pca/corrected pca space
#' @param reduction Dimensional reduction to use for corrected space
#' @param reduced.dims Number of reduced dimensions to use
#' @param orig.dims Number of PCs to use in original space
#' @param verbose Display progress bar
#'
#' @return Returns the average preservation metric
#'
#' @importFrom RANN nn2
#' @importFrom utils txtProgressBar setTxtProgressBar
#'
#' @export
#'
LocalStruct <- function(
  object,
  grouping.var,
  idents = NULL,
  neighbors = 100,
  reduction = "pca",
  reduced.dims = 1:10,
  orig.dims = 1:10,
  verbose = TRUE
) {
  if (is.null(x = idents)) {
    cells.use <- colnames(x = object)
  } else {
    cells.use <- WhichCells(object = object, idents = idents)
  }
  Idents(object = object) <- grouping.var
  local.struct <- list()
  ob.list <- SplitObject(object = object, split.by = grouping.var)
  if (verbose) {
    pb <- txtProgressBar(
      min = 1,
      max = length(x = ob.list),
      style = 3,
      file = stderr()
    )
  }
  embeddings <- Embeddings(object = object[[reduction]])[, reduced.dims]

  for (i in 1:length(x = ob.list)) {
    ob <- ob.list[[i]]
    ob <- FindVariableFeatures(
      object = ob,
      verbose = FALSE,
      selection.method = "dispersion",
      nfeatures = 2000
    )
    ob <- ScaleData(
      object = ob,
      features = VariableFeatures(object = ob),
      verbose = FALSE
    )
    ob <- RunPCA(
      object = ob,
      features = VariableFeatures(object = ob),
      verbose = FALSE,
      npcs = max(orig.dims)
    )
    ob.cells <- intersect(x = cells.use, y = colnames(x = ob))
    if (length(x = ob.cells) == 0) next
    nn.corrected <- nn2(
      data = embeddings[colnames(x = ob), ],
      query = embeddings[ob.cells, ],
      k = neighbors
    )$nn.idx
    nn.orig <- nn2(
      data = Embeddings(object = ob[["pca"]])[, orig.dims],
      query = Embeddings(object = ob[["pca"]])[ob.cells, orig.dims],
      k = neighbors
    )$nn.idx
    local.struct[[i]] <- sapply(X = 1:nrow(x = nn.orig), FUN = function(x) {
      length(x = intersect(x = nn.orig[x, ], y = nn.corrected[x, ])) / neighbors
    })
    if (verbose) {
      setTxtProgressBar(pb = pb, value = i)
    }
  }
  names(x = local.struct) <- names(x = ob.list)
  return(local.struct)
}

#' Calculates a mixing metric
#'
#' Here we compute a measure of how well mixed a composite dataset is. To
#' compute, we first examine the local neighborhood for each cell (looking at
#' max.k neighbors) and determine for each group (could be the dataset after
#' integration) the k nearest neighbor and what rank that neighbor was in the
#' overall neighborhood. We then take the median across all groups as the mixing
#' metric per cell.
#'
#' @param object Seurat object
#' @param grouping.var Grouping variable for dataset
#' @param reduction Which dimensionally reduced space to use
#' @param dims Dimensions to use
#' @param k Neighbor number to examine per group
#' @param max.k Maximum size of local neighborhood to compute
#' @param eps Error bound on the neighbor finding algorithm (from RANN)
#' @param verbose Displays progress bar
#'
#' @return Returns a vector of values representing the entropy metric from each
#' bootstrapped iteration.
#'
#' @importFrom RANN nn2
#' @importFrom pbapply pbsapply
#' @importFrom future.apply future_sapply
#' @importFrom future nbrOfWorkers
#' @export
#'
MixingMetric <- function(
  object,
  grouping.var,
  reduction = "pca",
  dims = 1:2,
  k = 5,
  max.k = 300,
  eps = 0,
  verbose = TRUE
) {
  my.sapply <- ifelse(
    test = verbose && nbrOfWorkers() == 1,
    yes = pbsapply,
    no = future_sapply
  )
  embeddings <- Embeddings(object = object[[reduction]])[, dims]
  nn <- nn2(
    data = embeddings,
    k = max.k,
    eps = eps
  )
  group.info <- object[[grouping.var, drop = TRUE]]
  groups <- unique(x = group.info)
  mixing <- my.sapply(
    X = 1:ncol(x = object),
    FUN = function(x) {
      sapply(X = groups, FUN = function(y) {
        which(x = group.info[nn$nn.idx[x, ]] == y)[k]
      })
    }
  )
  mixing[is.na(x = mixing)] <- max.k
  mixing <- apply(
    X = mixing,
    MARGIN = 2,
    FUN = median
  )
  return(mixing)
}

#' Prepare an object list that has been run through SCTransform for integration
#'
#' @param object.list A list of objects to prep for integration
#' @param assay Name or vector of assay names (one for each object) that correspond
#' to the assay that SCTransform has been run on. If NULL, the current default
#' assay for each object is used.
#' @param anchor.features Can be either:
#' \itemize{
#'   \item{A numeric value. This will call \code{\link{SelectIntegrationFeatures}}
#'   to select the provided number of features to be used in anchor finding}
#'   \item{A vector of features to be used as input to the anchor finding
#'   process}
#' }
#' @param sct.clip.range Numeric of length two specifying the min and max values
#' the Pearson residual will be clipped to
#' @param verbose Display output/messages
#'
#' @return An object list with the \code{scale.data} slots set to the anchor
#' features
#'
#' @importFrom pbapply pblapply
#' @importFrom methods slot slot<-
#' @importFrom future nbrOfWorkers
#' @importFrom future.apply future_lapply
#'
#' @export
#'
PrepSCTIntegration <- function(
  object.list,
  assay = NULL,
  anchor.features = 2000,
  sct.clip.range = NULL,
  verbose = TRUE
) {
  my.lapply <- ifelse(
    test = verbose && nbrOfWorkers() == 1,
    yes = pblapply,
    no = future_lapply
  )
  assay <- assay %||% sapply(X = object.list, FUN = DefaultAssay)
  assay <- rep_len(x = assay, length.out = length(x = object.list))
  objects.names <- names(x = object.list)
  object.list <- lapply(
    X = 1:length(x = object.list),
    FUN = function(i) {
      DefaultAssay(object = object.list[[i]]) <- assay[i]
      return(object.list[[i]])
