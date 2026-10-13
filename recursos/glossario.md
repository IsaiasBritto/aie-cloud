# Glossário — Cloud em PT-BR

Termos que aparecem nas aulas, com a tradução prática e o equivalente nas três grandes nuvens.

| Termo (EN) | PT-BR | AWS (esta disciplina) | Azure | GCP |
|------------|-------|-----|-------|-----|
| Region | Região | Region (`us-east-1`) | Region | Region |
| Availability Zone | Zona de disponibilidade | Availability Zone | Availability Zone | Zone |
| Virtual Machine | Máquina Virtual | EC2 | VM | Compute Engine |
| Object Storage | Armazenamento de Objetos | S3 | Blob Storage | Cloud Storage |
| Managed SQL Database | Banco relacional gerenciado | RDS (PostgreSQL + pgvector) | Azure SQL | Cloud SQL |
| NoSQL | Banco NoSQL | DynamoDB | Cosmos DB | Firestore |
| Function / FaaS | Função serverless | Lambda (+ Function URL) | Azure Functions | Cloud Functions |
| Containers sem servidor | Containers gerenciados | ECS Fargate · App Runner | Container Apps · ACI | Cloud Run |
| Container Registry | Registro de imagens | ECR | ACR | Artifact Registry |
| Managed Kubernetes | Kubernetes gerenciado | EKS | AKS | GKE |
| Identity / IAM | Identidade e acesso | IAM (roles; no Learner Lab, `LabRole`) | Entra ID + RBAC | IAM |
| Workload identity | Identidade do workload | task role / execution role | Managed Identity | Service Account |
| Secrets Manager | Cofre de segredos | Secrets Manager | Key Vault | Secret Manager |
| Speech / Language / Vision | Serviços cognitivos | Transcribe · Polly · Comprehend · Rekognition | AI Services (Speech, Language, Vision) | Speech/NL/Vision AI |
| LLM gerenciado | Modelos de fundação | Amazon Bedrock | Azure OpenAI / Foundry | Vertex AI |
| ML Platform | Plataforma de ML | SageMaker AI | Azure Machine Learning | Vertex AI |
| Observability | Observabilidade | CloudWatch (Logs, Metrics, Logs Insights) | Azure Monitor + App Insights | Cloud Monitoring |
| Cost Management | Gestão de custos | Cost Explorer · Budgets · Trusted Advisor | Cost Management · Advisor | Cost Management |
| Resource grouping | Agrupamento de recursos | tags + Resource Groups / Tag Editor | Resource Group | Project + labels |
| Cloud shell | Terminal no navegador | CloudShell | Cloud Shell | Cloud Shell |
| IaC | Infraestrutura como Código | CloudFormation | Bicep / ARM | Deployment Manager |
| Cross-cloud IaC | IaC multi-nuvem | Terraform | Terraform | Terraform |

------------|-------|-------|-----|-----|
| Region | Região | Region | Region | Region |
| Availability Zone | Zona de disponibilidade | Availability Zone | Availability Zone | Zone |
| Virtual Machine | Máquina Virtual | VM | EC2 | Compute Engine |
| Object Storage | Armazenamento de Objetos | Blob Storage | S3 | Cloud Storage |
| Managed Database | Banco gerenciado | Azure SQL / Cosmos DB | RDS / DynamoDB | Cloud SQL / Firestore |
| Function / FaaS | Função serverless | Azure Functions | Lambda | Cloud Functions |
| Container Registry | Registro de imagens | ACR | ECR | Artifact Registry |
| Managed Kubernetes | Kubernetes gerenciado | AKS | EKS | GKE |
| Identity / IAM | Identidade e acesso | Entra ID + RBAC | IAM | IAM |
| Secrets Manager | Cofre de segredos | Key Vault | Secrets Manager | Secret Manager |
| Cost Management | Gestão de custos | Cost Management | Cost Explorer | Cost Management |
| IaC | Infraestrutura como Código | Bicep / ARM | CloudFormation | Deployment Manager |
| Cross-cloud IaC | IaC multi-nuvem | Terraform | Terraform | Terraform |

---

## Acrônimos frequentes

- **IaaS** — Infrastructure as a Service (você controla VM, SO, runtime)
- **PaaS** — Platform as a Service (provedor cuida do SO/runtime; você cuida do app)
- **SaaS** — Software as a Service (provedor cuida de tudo; você usa)
- **IaC** — Infrastructure as Code
- **RBAC** — Role-Based Access Control
- **IAM** — Identity and Access Management
- **SigV4** — Signature Version 4, a assinatura de toda requisição à API da AWS
- **HA** — High Availability (alta disponibilidade)
- **SLA** — Service Level Agreement
- **RPO / RTO** — Recovery Point Objective / Recovery Time Objective
- **FinOps** — Cloud Financial Operations (gestão financeira de nuvem)
- **MLOps** — Machine Learning Operations
- **LLMOps** — Large Language Model Operations
