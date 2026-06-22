# ML Production Pipeline Proposal

## Purpose
Guidance for evolving from notebook-centric experimentation to a production-grade ML pipeline using AWS-managed services (S3, Glue/Athena, SageMaker Processing/Training, Feature Store, Pipelines, Model Registry, Clarify, Model Monitor, Endpoints, CloudWatch).

## Goals
- Ensure reproducible, auditable ML workflows aligned with fraud detection SLOs.
- Separate research-friendly notebooks from automated pipelines that feed production.
- Standardize artefacts (datasets, models, metrics, approvals) across environments (dev/stg/prd).
- Enable continuous training/monitoring loops integrated with CI/CD and IaC.

## Reference Architecture
1. **Data Foundation**
   - Raw events land in `S3` bronze buckets, catalogued via `Glue` tables and queried with `Athena`.
   - Data quality rules (Great Expectations/Deequ) run in `SageMaker Processing` jobs to validate incoming batches.
2. **Feature Engineering**
   - Deterministic transformations expressed as Python scripts or Data Wrangler exports executed in Processing jobs.
   - Validated features registered in `SageMaker Feature Store` (offline & online stores) with metadata (ownership, lineage, PII classification).
3. **Training & Evaluation**
   - `SageMaker Pipelines` orchestrate Processing → Training → Evaluation → Conditional approval.
   - Training step launches managed containers (e.g., XGBoost, custom Docker) on spot/on-demand instances.
   - `Clarify` steps check bias/drift; metrics logged to `CloudWatch` and stored with the model package.
4. **Model Registry & Deployment**
   - Successful runs register artefacts in `Model Registry` with metadata (dataset version, hyperparameters, evaluation metrics).
   - Promotion to staging/production triggered via CI/CD approval gates, deploying to `SageMaker Endpoints` (real-time) or `Batch Transform`.
   - ECS/API Gateway layer handles request orchestration, caching, and SLA guardrails.
5. **Monitoring & Retraining**
   - `Model Monitor` schedules capture jobs for data quality, model quality, bias, and drift; alerts routed through CloudWatch alarms.
   - KPIs (AUC-PR, recall@threshold, latency) tracked in dashboards (CloudWatch, QuickSight, Grafana).
   - Retraining pipelines triggered when drift thresholds or business triggers fire.
6. **Governance & Observability**
   - All jobs emit structured logs with `trace_id` for cross-service correlation.
   - IaC (Terraform/CDK) codifies infrastructure, roles, networking, encryption (KMS).
   - Access managed via IAM least privilege; artefacts versioned in Git with PR-based approvals.

## Transition from Notebooks
| Aspect | Notebook-Only | Managed Pipeline |
|--------|---------------|------------------|
| Reproducibility | Dependent on author environment | Deterministic executions logged with inputs/outputs |
| Collaboration | Hard to review/merge at scale | Code reviews, tests, CI/CD pipelines |
| Governance | Limited audit trail | Versioned artefacts, approvals, CloudTrail events |
| Automation | Manual reruns | Scheduled/triggered workflows, retraining gates |
| Cost Control | Easy to leave instances running | Jobs scoped per task, tracked via billing tags |
| Experimentation Speed | Fast ad-hoc exploration | Slightly slower to iterate but encourages modular design |

### Recommended Workflow
1. Use notebooks/Data Wrangler for **exploration/prototyping**; export final logic as scripts (`src/processing/*.py`) committed to repo.
2. Parameterize scripts with config files (YAML/JSON) to support multiple datasets/environments.
3. Package dependencies via `requirements.txt`/`pip install -r`; build Docker images if custom libs are required.
4. Write unit/integration tests (pytest) for feature transformations and training pipelines.
5. Define `SageMaker Pipeline` in code (SM SDK) and orchestrate via CI/CD (CodePipeline, GitHub Actions) triggered on merges to main.
6. Register artefacts and enforce manual approval for production promotion.
7. Keep notebooks in `notebooks/` purely for reports/visualization; documented to point to the corresponding pipeline scripts.

## Implementation Phases
| Phase | Focus | Deliverables |
|-------|-------|--------------|
| P0 | Foundations | Repo structure, IaC baseline, baseline dataset catalogued |
| P1 | Processing Layer | Data validation jobs, feature scripts, Feature Store setup |
| P2 | Training Pipeline | SageMaker Pipeline definition, automated metrics, Model Registry integration |
| P3 | Deployment Automation | CI/CD pipeline, endpoint provisioning, canary deploy strategy |
| P4 | Monitoring | Model Monitor schedules, CloudWatch dashboards, alert policies |
| P5 | Continuous Ops | Retraining triggers, cost dashboards, documentation/runbooks |

## Pros & Cons Summary
- **Pros**: reproducibility, compliance, shared feature assets, automated deploy, SLA consistency, easier incident response.
- **Cons**: higher initial investment, more DevOps expertise required, pipeline rigidity (changes need code reviews), additional cost for managed services.

## Open Considerations
- Choice between `Step Functions` vs pure `SageMaker Pipelines` for orchestrating cross-service tasks (e.g., triggering ECS jobs).
- Integration with existing CI/CD tooling (GitHub Actions vs CodePipeline) and secrets management (Secrets Manager, Parameter Store).
- Definition of approval policy in Model Registry (auto vs manual, thresholds).
- Strategy for local development (Docker compose, SM local mode) to avoid long feedback loops.

## Next Steps
- Review this proposal with engineering, data science, DevOps stakeholders and capture decisions inline.
- Identify existing notebooks that should be refactored first; mark owners and deadlines.
- Draft IaC modules for SageMaker pipelines/endpoints consistent with `infra/` conventions.
- Define minimum governance artefacts (runbook, RACI, SLAs) before production rollout.
