export interface GlobalStats {
    total_patents: number;
    total_portfolios: number;
    blocking_events: string;
    ml_models: number;
    models_status: {
        "3y": boolean;
        "5y": boolean;
    };
}
