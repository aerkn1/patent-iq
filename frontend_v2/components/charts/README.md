# Chart Layer

Shared chart components should be split by engine:

1. `recharts/` for compact analytics
2. `echarts/` for dense analytics and structure views
3. `visx/` for product-specific geometry

Page components should consume wrappers from these folders instead of instantiating raw chart libraries directly in workspace files.
