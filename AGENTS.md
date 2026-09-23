# SmartPark AI contributor rules

- Never create fake AI results, hardcoded occupancy, random status values, or placeholder statistics.
- Keep YOLO detection and parking-region matching in `services/`; Flask routes only coordinate requests and responses.
- Keep persistence in `database_models/` and preserve existing migrations/data where applicable.
- Use configured parking-space polygons; never hardcode parking coordinates in Python.
- Test changed functionality before reporting it complete.
- Use simple, maintainable Python with type hints and clear errors.
- Preserve working functionality unless a change is explicitly requested.
- Do not add unnecessary frameworks or infrastructure.
