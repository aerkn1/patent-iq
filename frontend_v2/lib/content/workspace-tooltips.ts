export const workspaceTooltipCopy = {
  overview: {
    familyStatusDistribution:
      "Share of in-scope families by current lifecycle status in the selected portfolio.",
    inScopeFamiliesInChart:
      "Visible family denominator included in this status chart after unclassified families and suppressed statuses are excluded.",
    fullyActive:
      "Families with at least one active branch and no lapsed-only outcome across the family.",
    partiallyLapsed:
      "Families that still have active coverage but also contain lapsed or expired branches.",
    dead: "Families with no active coverage remaining.",
    blockingLeaderFamilies:
      "Portfolio families ranked by blocking score within the current overview slice.",
    topFieldConcentration:
      "Largest field exposures in the portfolio based on family concentration.",
    topCitingOwners:
      "External owners generating the most citation pressure on the portfolio in the current overview slice.",
    filingChronology:
      "Year-by-year family filings in the portfolio by priority year.",
    latestFilingYear:
      "Most recent filing year returned in the displayed filing chronology.",
    peakFilingYear:
      "Returned year with the highest family filing count in the displayed chronology.",
    latestThreeYearWindow:
      "Trailing three priority years of family filings in the displayed chronology.",
    annualFamilyFilings:
      "Number of portfolio families with priority year in the shown year.",
    rollingThreeYearFilings:
      "Sum of family filings across the trailing three priority years.",
    cumulativeFamilies:
      "Running total of portfolio families across filing years.",
    filingBuildup:
      "Combined filing view showing annual filings, trailing three-year filings, and cumulative family growth.",
    familyStatusChronology:
      "Year-by-year replay of current portfolio families grouped by lifecycle status.",
    latestYear:
      "Most recent returned year in the displayed chronology.",
    lapsedAndDead:
      "Partially lapsed plus dead families in the latest returned year.",
    statusMixOverTime:
      "Historical family counts by status in the current portfolio replay.",
    jurisdictionUnlockChronology:
      "First observed jurisdiction years plus yearly office-state reach for the current portfolio replay.",
    unlockedJurisdictions:
      "Distinct jurisdictions ever observed for the in-scope portfolio families.",
    latestActiveGrantedReach:
      "Jurisdictions classified as active or grant-backed in the latest returned year.",
    latestLapsedReach:
      "Jurisdictions classified as lapsed in the latest returned year.",
    activeGranted:
      "Jurisdictions with at least one active or grant-backed branch in the shown year.",
    pending:
      "Jurisdictions with pending branch presence in the shown year and no active or grant-backed classification.",
    lapsed:
      "Jurisdictions with lapsed-only presence in the shown year and no active or pending classification.",
    newUnlocks:
      "Jurisdictions first observed for the portfolio in the shown year.",
    unlockLog:
      "Jurisdiction codes first observed in the shown year.",
    jurisdictionStateMix:
      "Year-by-year office-state reach showing active or granted, pending, and lapsed jurisdictions.",
  },
  forecast: {
    pendingGrantPipeline:
      "Model-based view of currently pending branches and their estimated grant likelihood.",
    expectedLikelyGrants:
      "Sum of modeled grant likelihood across the displayed pending-branch scope.",
    scoredPendingBranches:
      "Current pending families and branches that received model scores in the selected forecast layer.",
    currentPendingCoverage:
      "Share of current pending families and branches covered by the scored forecast dataset.",
    byOffice:
      "Grouped pending-grant summary by jurisdiction or office.",
    byField:
      "Grouped pending-grant summary by portfolio field.",
    topScoredPendingBranches:
      "Highest-ranked pending branches in the current forecast slice.",
    office:
      "Patent office or jurisdiction attached to the grouped pending branches.",
    avgProbability:
      "Mean modeled grant probability across the displayed rows or group.",
    families:
      "Distinct portfolio families represented in the displayed group.",
    jurisdiction:
      "Patent office or jurisdiction attached to the pending branch.",
    field:
      "Portfolio field assigned to the pending branch or grouped view.",
    rank:
      "Office-relative ordering of the branch within the selected forecast horizon.",
    family:
      "DOCDB family identifier for the scored pending branch.",
    priority:
      "Planning priority tier assigned to the scored pending branch.",
    grantProbability:
      "Modeled probability that the pending branch will grant within the selected forecast horizon.",
    percentile:
      "Relative position of the branch's grant probability within its office-specific scored population.",
    blocking:
      "Family-level blocking score attached to the branch's family.",
  },
  citation: {
    citationSummary:
      "Portfolio-level citation totals and breadth for the selected owner and year.",
    forwardCitingFamilies:
      "Distinct external citing families across the portfolio's forward citation edge set.",
    forwardCitationEvents:
      "Clean forward citation edges into the portfolio after cleaning filters.",
    backwardCitedFamilies:
      "Distinct patent families cited by the portfolio across the backward citation edge set.",
    backwardCitationEvents:
      "Clean backward patent citation edges from the portfolio family set.",
    backwardNplCitations:
      "Backward non-patent literature references linked to the portfolio.",
    citingOwnerDiversity:
      "Average diversity of external citing owners across the portfolio summary layer.",
    citationChronology:
      "Year-by-year forward citation history for the portfolio, with projected continuation beyond the observed range.",
    latestYear:
      "Most recent observed year returned in the citation chronology.",
    observedCitations:
      "Forward citation events observed in the returned historical series.",
    projection3y:
      "Projected forward citation level three years beyond the latest observed year.",
    projection5y:
      "Projected forward citation level five years beyond the latest observed year.",
    forecastContributorTable:
      "Top entities contributing to the selected citation forecast horizon.",
    contributor:
      "Entity included in the forecast-contributor breakdown for the selected horizon.",
    contribution:
      "Amount added by the listed contributor to the selected forecast horizon output.",
    share:
      "Contributor share of the selected forecast horizon output.",
    citationQualityAndShape:
      "Portfolio-level citation profile metrics derived from the citation summary layer.",
    generality:
      "Average breadth of technology areas represented by later citing families.",
    originality:
      "Average breadth of technology areas represented in the portfolio's backward citation base.",
    scienceGrounding:
      "Average science-linkage score derived from backward non-patent literature presence.",
    citingFamilyDepth:
      "Average number of distinct citing families connected to portfolio families.",
    ownerDiversity:
      "Average diversity of external citing owners across portfolio families.",
    attackerDensity:
      "Average concentration of external citation pressure around portfolio families.",
    impactDrivers:
      "Portfolio families ranked by citation pull and blocking strength.",
    field:
      "Portfolio field assigned to the displayed family or citation slice.",
    lifecycle:
      "Current family status used in the displayed portfolio view.",
    sort:
      "Ranking metric applied to the current cited-family list.",
    forwardCitations:
      "Clean forward citation events attached to the displayed family or slice.",
    forwardWeighted:
      "Weighted forward citation total attached to the displayed family or slice.",
    earlyCitations5y:
      "Forward citations accumulated within the family's first five years.",
    earlyCitations7y:
      "Forward citations accumulated within the family's first seven years.",
    blocking:
      "Family-level blocking score used across portfolio ranking views.",
    rank:
      "Position of the row within the current ranked slice.",
    family:
      "DOCDB family identifier for the displayed row.",
    primaryField:
      "Primary portfolio field assigned to the displayed family.",
    priorityYear:
      "Earliest priority year of the displayed family.",
    topCitingOwners:
      "External owners ranked by citation pressure against the portfolio.",
    pressure:
      "Weighted citation pressure attributed to the displayed slice.",
    citations:
      "Citation events attributed to the displayed slice.",
    lastSeen:
      "Most recent year the displayed row appears in the returned citation slice.",
    families:
      "Distinct portfolio families represented in the displayed slice.",
    year:
      "Citation year used to constrain the returned slice.",
    topCitationFields:
      "Fields receiving the most external citation pressure against the portfolio.",
    owners:
      "Distinct citing owners represented in the displayed slice.",
    topCitationJurisdictions:
      "Jurisdictions receiving the most external citation pressure against the portfolio.",
    jurisdictions:
      "Jurisdiction code attached to the displayed citation slice.",
    fields:
      "Distinct portfolio fields represented in the displayed slice.",
    topCitedCpcGroups:
      "CPC groups most represented in the cited-side citation mix.",
    cpcMainGroup:
      "CPC main group attached to the cited-side citation slice.",
    events:
      "Citation events linked to the displayed slice.",
    citedFamilies:
      "Distinct cited families represented in the displayed slice.",
  },
  fields: {
    fieldFootprint:
      "Portfolio family distribution across the main field taxonomy.",
    leadingField:
      "Field with the largest family share in the current portfolio view.",
    topThreeFields:
      "Combined family share of the three largest fields in the portfolio.",
    familyShare:
      "Share of in-scope portfolio families assigned to the displayed field or segment.",
    activeShare:
      "Share of field families that are currently fully active.",
    classificationMix:
      "Ranked field composition view for the current portfolio.",
    classificationView:
      "Field-share ranking for the current classification scope.",
    segment:
      "Classification segment shown in the current view.",
    field:
      "Portfolio field shown in the current field view.",
    scope:
      "Current field scope used for the classification view.",
    trajectory:
      "Current direction of field-share movement in the returned chronology layer.",
    movement:
      "Magnitude and direction bucket of recent field-share change.",
    gainLedSegments:
      "Segments currently classified with gain-oriented movement.",
    lossLedSegments:
      "Segments currently classified with loss-oriented movement.",
    flatSegments:
      "Segments currently classified with flat movement.",
    families:
      "Number of portfolio families assigned to the displayed field or slice.",
    fieldChronology:
      "Year-by-year field mix history for the portfolio.",
    allFieldActivity:
      "Historical field activity across the full portfolio view.",
    selectedFieldHistory:
      "Historical share of the currently selected field.",
    year:
      "Returned year in the field chronology.",
    share:
      "Field share of the portfolio in the shown year.",
    topCitingOwners:
      "External owners exerting the most citation pressure within the selected field view.",
    pressure:
      "Weighted citation pressure attributed to the displayed owner or field slice.",
    citations:
      "Citation events attributed to the displayed owner or family slice.",
    lastSeen:
      "Most recent year the displayed row appears in the selected field slice.",
    mostCitedFamilies:
      "Portfolio families receiving the most citation attention within the selected field view.",
    forwardCitations:
      "Clean forward citation events attached to the displayed family.",
    earlyCitations7y:
      "Forward citations accumulated within the family's first seven years.",
    blocking:
      "Family-level blocking score used across portfolio ranking views.",
    lifecycle:
      "Current family status used in the displayed field view.",
    priorityYear:
      "Earliest priority year of the displayed family.",
  },
  families: {
    portfolioFamilies:
      "Ranked family list for the current portfolio with lifecycle, field, and blocking context.",
    search:
      "Search the current family slice by family identifier, field, or lifecycle text.",
    lifecycle:
      "Current family status used in the displayed portfolio view.",
    primaryField:
      "Primary portfolio field assigned to the displayed family.",
    sortBy:
      "Ranking rule applied to the current family table.",
    family:
      "DOCDB family identifier for the displayed row.",
    title:
      "Family title used in the current portfolio family view.",
    priorityYear:
      "Earliest priority year of the displayed family.",
    blocking:
      "Family-level blocking score used across portfolio ranking views.",
  },
  tabs: {
    overview:
      "Portfolio overview with current status mix, filing chronology, and jurisdiction reach.",
    families:
      "Ranked portfolio family list with lifecycle, field, and blocking context.",
    fields:
      "Field structure, chronology, and field-scoped citation views.",
    citation:
      "Portfolio citation breadth, chronology, and pressure breakdowns.",
    forecast:
      "Pending-grant outlook and branch-level probability views.",
  },
  familyView: {
    tabPublications:
      "Family publication set, stage mix, and member-publication drilldown.",
    tabLegal:
      "Current legal footprint, yearly legal replay, and blocking durability views.",
    tabFields:
      "Current field footprint, classification map, and field trajectory views.",
    tabCitation:
      "Family citation summary, chronology, leaderboards, and citing-family detail.",
    methodology:
      "Support notes and scope caveats attached to the active family view.",
    familyProfile:
      "Core family profile metrics and peer-ranked quality signals for the selected family.",
    memberPublications:
      "Current publication set for the family, including office, kind, and stage indicators.",
    publicationMix:
      "Visible family publication mix by office and publication stage.",
    publication:
      "Publication identifier in the current family member set.",
    office:
      "Patent office or authority attached to the displayed publication or slice.",
    kind:
      "Publication kind code in the displayed publication set.",
    publicationDate:
      "Publication date for the displayed family member.",
    application:
      "Whether the displayed publication is treated as an application-stage record.",
    grant:
      "Whether the displayed publication is treated as a grant-stage record.",
    branchStateMix:
      "Current branch-state distribution across the tracked family jurisdictions.",
    trackedJurisdictions:
      "Jurisdictions currently tracked in the family legal footprint.",
    leadBranchState:
      "Most prevalent current branch-state label across the tracked jurisdictions.",
    stateBands:
      "Distinct visible branch-state groups in the current family legal footprint.",
    jurisdictions:
      "Jurisdiction code attached to the displayed family legal row or slice.",
    branchState:
      "Current legal branch-state label attached to the displayed family jurisdiction row.",
    jurisdictionLegalFootprint:
      "Current jurisdiction-level legal share and contribution within the family footprint.",
    leadJurisdiction:
      "Jurisdiction contributing the largest current legal share within the family footprint.",
    familyLegalShare:
      "Current jurisdiction share of the family's legal footprint.",
    legalContribution:
      "Raw contribution of the jurisdiction to the current family legal footprint.",
    strengthBand:
      "Relative legal-strength band assigned to the displayed jurisdiction.",
    lastEvent:
      "Latest dated legal event recorded for the displayed jurisdiction or family row.",
    legalHistory:
      "Year-by-year legal replay for the family from yearly status snapshots.",
    observedSpan:
      "First and latest returned years in the displayed family chronology.",
    latestStatus:
      "Latest returned family legal status in the displayed chronology.",
    lastDatedEvent:
      "Latest dated legal event recorded in the active family legal summary.",
    year:
      "Returned year in the displayed family chronology or history table.",
    status:
      "Family status or support label in the displayed chronology view.",
    activeJurisdictions:
      "Jurisdictions with active family presence in the shown year.",
    activeGrantBranches:
      "Grant-backed branches that remain active in the shown year.",
    lapsedJurisdictions:
      "Jurisdictions with lapsed family presence in the shown year.",
    opposedBranches:
      "Opposed branches recorded in the shown year.",
    sevenYearWindow:
      "Whether the seven-year forward citation window is closed for the shown year.",
    historicalSafety:
      "Whether the displayed historical citation row is marked safe for chronology use.",
    blockingTrajectory:
      "Year-by-year blocking and legal-score history for the family.",
    latestBlocking:
      "Most recent blocking score returned in the family blocking history.",
    latestLegal:
      "Most recent legal enforceability score returned in the family blocking history.",
    blockingScore:
      "Family-level blocking score used across family and portfolio ranking views.",
    legalEnforceability:
      "Family legal enforceability score in the displayed historical or current view.",
    fieldFootprint:
      "Current field and CPC footprint attached to the family.",
    primaryField:
      "Primary WIPO field assigned to the family in the displayed snapshot.",
    breadthBand:
      "Current classification breadth band attached to the family.",
    topCpcMainGroup:
      "Highest-share CPC main group in the displayed family footprint.",
    leadFieldShare:
      "Largest current field share observed in the family footprint.",
    ipcCpcMap:
      "Current IPC and CPC classification map attached to the family.",
    ipcSubclasses:
      "IPC subclass codes currently attached to the family.",
    cpcSections:
      "CPC sections currently attached to the family.",
    cpcSubclasses:
      "CPC subclass codes currently attached to the family.",
    cpcMainGroups:
      "CPC main groups currently attached to the family.",
    cpcSubclass:
      "Displayed CPC subclass in the family classification map.",
    fieldTrajectory:
      "Historical field-share evolution for the family.",
    trackedYears:
      "Returned years covered by the displayed field history.",
    trackedFields:
      "Distinct fields represented in the displayed family history.",
    latestLeadField:
      "Latest leading field in the displayed family history.",
    classificationChronology:
      "Historical yearly classification snapshot for the family.",
    topCpcShare:
      "Share of the displayed top CPC main group within the family footprint.",
    currentFieldContributions:
      "Current legal and heritage contribution split across family fields.",
    legalContributionShare:
      "Current field share of raw legal contribution within the family.",
    heritageContributionShare:
      "Current field share of raw heritage contribution within the family.",
    citationSummary:
      "Current family citation summary across forward, backward, and owner-breadth metrics.",
    forwardCitationEvents:
      "Forward citation events attached to the family before family-level deduping.",
    forwardCleanCitationEvents:
      "Clean forward citation events attached to the family after citation cleaning filters.",
    rawCitingFamilies:
      "Raw citing-family breadth attached to the family before the cleaned distinct citation view.",
    citationChronology:
      "Year-by-year family citation history with optional forecast overlay.",
    latestDistinctForwardCitationCount:
      "Most recent distinct forward citation count returned in the family chronology.",
    latestDistinctBackwardCitationCount:
      "Most recent distinct backward citation count returned in the family chronology.",
    distinctForwardCitationCount:
      "Distinct forward citing families attached to the family in the displayed year or row.",
    distinctForwardCitationCount7y:
      "Distinct forward citing families accumulated within the family's first seven years.",
    distinctForwardOwnerCount:
      "Distinct external citing owners attached to the family in the displayed year or row.",
    distinctBackwardCitationCount:
      "Distinct cited patent families attached to the family in the displayed year or row.",
    weightedCitationMass:
      "Weighted forward citation total attached to the family.",
    citingFamilies5y:
      "Distinct citing families accumulated within the family's first five years.",
    latestForwardCitationDate:
      "Latest observed forward citation date in the displayed family chronology or row.",
    backwardCitationEvents:
      "Backward citation events attached to the family before family-level deduping.",
    backwardCleanCitationEvents:
      "Clean backward citation events attached to the family after citation cleaning filters.",
    distinctBackwardOwnerCount:
      "Distinct cited owners attached to the family in the displayed summary layer.",
    distinctBackwardNplCitationCount:
      "Distinct backward non-patent literature citations attached to the family.",
    topCitingOwners:
      "External owners ranked by citation pressure or citation breadth against the family.",
    pressure:
      "Threat-weighted clean citation pressure attributed to the displayed owner or slice.",
    citedFamilyMembers:
      "Distinct family members touched by the displayed citing-owner slice.",
    citationLeaderboards:
      "Publication-level citation leaderboards attached to the family.",
    topCitedPublications:
      "Most-cited family publications in the current family evidence view.",
    topCitedFamilyMembers:
      "Ranked list of family-member publications by forward citation breadth.",
    citingFamilies:
      "Clean external families citing the selected family.",
    ownerFilter:
      "Filter the citing-family list by current citing owner name.",
    citingFamily:
      "External DOCDB family identifier citing the selected family.",
    citingOwner:
      "Current owner name attached to the displayed citing family row.",
    distinctCitedFamilyMemberCount:
      "Distinct cited family members touched by the displayed citing family.",
    distinctCitingPublicationCount:
      "Distinct citing publications contributed by the displayed citing family.",
    firstSeen:
      "Earliest observed citation date in the displayed citing-family or citation row.",
    latestSeen:
      "Most recent observed citation date in the displayed row.",
  },
  marketView: {
    overview:
      "Market-wide pulse and field league table for the bounded market workspace.",
    fieldAnalysis:
      "Selected-field drilldown for competition, jurisdiction, and technology views.",
    competition:
      "Owner presence, citation pressure, and attacker views for the selected field.",
    jurisdictionsAndGrants:
      "Jurisdiction footprint plus application and grant flow for the selected field.",
    technology:
      "CPC structure, owners, and citing-owner views for the selected field.",
    marketWideChronology:
      "Year-by-year market stock and lifecycle mix across the bounded market universe.",
    familiesInScope:
      "Unique DOCDB families inside the bounded market universe for the latest supported year.",
    fullyActive:
      "Families that remain fully active across their current legal footprint in the latest supported year.",
    ownersInScope:
      "Distinct current owners represented across the bounded market family universe.",
    marketCrowding:
      "Market-wide crowding label derived from owner breadth and top-owner concentration.",
    fieldsInScope:
      "Served WIPO fields currently included in the market landscape workspace.",
    risingFields:
      "Fields whose latest comparable state still points to strengthening momentum.",
    coolingFields:
      "Fields whose latest comparable state points to weakening momentum versus the prior comparable year.",
    fieldScale:
      "Current family stock for the selected field, including all families assigned into this field slice.",
    activeShare:
      "Share of field families that are still active in at least one jurisdiction.",
    competitivePressure:
      "Distinct current owners represented in the selected field.",
    topOwnerShare:
      "Share of field families controlled by the single largest owner in the current field slice.",
    defensivePosture:
      "Average blocking density across the selected field footprint.",
    activeJurisdictionShare:
      "Average share of active jurisdictions across families in this field.",
    fieldBalance:
      "Field concentration measure attached to the selected field footprint.",
    momentum:
      "Latest year-over-year change in field family count for the selected field.",
    latestYear:
      "Most recent year available in the displayed market or field chronology.",
    currentFamilies:
      "Field family count in the latest available year for the selected field chronology.",
    marketMedian:
      "Median field family count across all served market fields in the same year.",
    vsMarketMedian:
      "Difference between the selected field's family count and the market-field median in the same year.",
    avgBlocking:
      "Average family blocking score across the unique bounded market family universe.",
    avgEnforceability:
      "Average family enforceability score across the unique bounded market family universe.",
    avgForwardCitations:
      "Average clean forward citations per family across the unique bounded market family universe.",
    crowding:
      "Latest market-wide crowding label derived from owner breadth and top-owner concentration.",
    pendingFiling:
      "Families still in pending or emerging filing stages in the displayed market year.",
    partiallyLapsed:
      "Families that keep some live rights while part of the jurisdiction footprint has already lapsed.",
    dead:
      "Families with no remaining active rights in the displayed market year.",
    shareOfMarketStock:
      "Share of the current bounded market family stock represented by the displayed status slice.",
    mixView:
      "Lifecycle-share view of the market chronology.",
    countsView:
      "Absolute family-count view of the market chronology.",
    latestSupportedYear:
      "Latest supported year returned in the current market chronology.",
    fieldLeagueTable:
      "Ranked field view across size, state, momentum, blocking density, and crowding.",
    field:
      "Displayed market field or selected field code in the current market view.",
    marketState:
      "Current market-state label attached to the displayed field.",
    families:
      "Family count in the displayed market slice.",
    blocking:
      "Blocking score or blocking density attached to the displayed market slice.",
    spark:
      "Recent field family-count mini-trend across the displayed sparkline window.",
    leadingJurisdictionsByField:
      "Top protection-footprint jurisdictions within each served field.",
    fieldFilter:
      "Field used to constrain the current market subview.",
    view:
      "Presentation mode used for the current market panel.",
    chartView:
      "Chart view of the current market slice.",
    tableView:
      "Tabular view of the current market slice.",
    pieView:
      "Pie view of the current market slice within one selected field.",
    jurisdiction:
      "Jurisdiction code attached to the displayed market slice.",
    active:
      "Active family count in the displayed market slice.",
    fieldShare:
      "Share of the selected field represented by the displayed slice.",
    marketFilters:
      "Controls for the bounded market landscape and selected field drilldown.",
    selectedField:
      "Currently selected field used for the field-specific market drilldown.",
    freshness:
      "Snapshot date of the market workspace data backing the current view.",
    selectedFieldSummary:
      "Current summary metrics for the selected field.",
    fieldRationale:
      "State rationale and evidence attached to the selected market field.",
    citationPressureChronology:
      "Year-by-year incoming citation activity into the selected field.",
    topOwnerPresence:
      "Current owner presence inside the selected field.",
    fieldShareView:
      "Owner presence view ranked by field share in the selected field.",
    avgBlockingView:
      "Owner presence view ranked by average blocking in the selected field.",
    totalBlocking:
      "Total blocking attributed to the displayed owner or family slice.",
    topFamiliesInSelectedField:
      "Highest-blocking families inside the selected market field.",
    fieldPresence:
      "Family presence share inside the selected field.",
    fieldPresenceWeight:
      "Normalized field-presence share attached to the displayed family.",
    status:
      "Current status label attached to the displayed market row.",
    topCitingOwners:
      "External owners citing into the selected field, ranked by attacker pressure.",
    topCitingJurisdictions:
      "Citing-side jurisdictions ranked by citation pressure against the selected field.",
    pressure:
      "Weighted citation pressure attributed to the displayed market slice.",
    citations:
      "Citation events attributed to the displayed market slice.",
    jurisdictions:
      "Distinct jurisdictions represented in the displayed market slice.",
    lastSeen:
      "Most recent year the displayed market row appears in the returned slice.",
    pressureIntensity:
      "Relative pressure scale for the displayed citing-owner row.",
    fieldFootprintByJurisdiction:
      "Unique family geography for the selected field across jurisdictions.",
    grantMixByOffice:
      "Current selected-year application and grant publication mix by office for the selected field.",
    applicationsAndGrantsByJurisdiction:
      "Year-by-year office event flow for the selected field.",
    applications:
      "Application publication count in the displayed market slice.",
    grants:
      "Grant publication count in the displayed market slice.",
    totalEvents:
      "Combined application and grant event count in the displayed market slice.",
    technologyFilters:
      "Selected-year controls applied across the technology views for the current field.",
    year:
      "Displayed market or technology year used to constrain the current slice.",
    topCpcGroupsInSelectedField:
      "Selected-year CPC ranking inside the chosen field.",
    cpcMainGroup:
      "CPC main group attached to the displayed market technology slice.",
    cpcShare:
      "Share of the CPC slice within the selected field or market view.",
    growth:
      "Growth metric attached to the displayed market technology slice.",
    heat:
      "Current heat-state label attached to the displayed CPC slice.",
    topOwnersByCpcMainGroup:
      "Selected-year owner concentration inside one CPC slice.",
    owner:
      "Owner attached to the displayed market row.",
    mostCitingOwnersBySelectedCpc:
      "Selected-year external citing owners into one CPC slice.",
    citingOwner:
      "External citing owner attached to the displayed CPC slice.",
    events:
      "Citation events linked to the displayed market slice.",
    eventShare:
      "Share of citation events represented by the displayed CPC slice.",
    citedFamilies:
      "Distinct cited families represented in the displayed CPC slice.",
    lethality:
      "Threat-weighted citation lethality attributed to the displayed CPC slice.",
    cpcGeographyWithinField:
      "CPC and jurisdiction slices inside the selected field for the chosen year.",
    sliceShare:
      "Share of the current CPC-jurisdiction slice represented by the displayed row.",
  },
} as const;
