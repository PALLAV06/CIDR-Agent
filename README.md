# Azure CIDR Agent

![Azure CIDR Agent Dashboard Screenshot](screenshot.png)

## 🚩 Problem Statement

Managing IP address space in large Azure environments is challenging.  
- **CIDR blocks** are often wasted due to over-provisioning or forgotten resources.
- **Subnet sprawl** and unused VNets lead to IP exhaustion and operational complexity.
- Azure’s native portal does not provide a holistic, interactive view of CIDR usage, nor actionable suggestions to free up IPs.

## 💡 Solution

**Azure CIDR Agent** is an interactive, Azure-authenticated dashboard that:
- Visualizes all used CIDRs, subnets, and VNets in your Azure subscription.
- Identifies VNets and subnets that can be safely deleted to free up IP space.
- Suggests optimal CIDR blocks for new VNets/subnets with zero IP wastage.
- Provides a modern, Azure Portal-inspired UI with light/dark theme support and animated feedback.

## ✨ Features

- **Live Azure Integration:** Uses Managed Identity or Service Principal for secure, real-time data.
- **Used CIDRs Overview:** See all VNets, subnets, and their CIDRs in a sortable, filterable table.
- **Free Up Suggestions:** Instantly find VNets with no subnets and subnets with no connected devices (0 IPs used).
- **CIDR Suggestion Engine:** Enter your desired subnet size and count; get the best-fit VNet CIDR and subnet plan.
- **Azure Portal UI:** Theming, colors, and layout match the Azure Portal for a seamless experience.
- **Performance:** Caching and refresh controls for fast, scalable operation.
- **Animations:** Lottie and CSS transitions for a delightful user experience.
- **One-click Deploy:** Docker and Azure Web App ready, with GitHub Actions CI/CD.

## 🏗️ Architecture

- **Frontend:** Streamlit, custom CSS, Lottie animations
- **Backend:** Python, Azure SDKs (`azure-identity`, `azure-mgmt-network`, `azure-mgmt-resource`)
- **Deployment:** Docker, Azure Web App for Containers, GitHub Actions

## 📊 Success Metrics

- **IP Space Reclaimed:** Number of CIDRs/subnets identified and freed.
- **User Time Saved:** Reduction in manual Azure Portal navigation and IP planning.
- **Zero Overlap:** All suggested CIDRs are guaranteed not to overlap with existing allocations.
- **Performance:** Dashboard loads in <3 seconds for 95% of user actions (with caching).
- **Security:** No credentials stored in code; uses Azure Managed Identity or GitHub Secrets.

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/your-org/azure-cidr-agent.git
cd azure-cidr-agent
pip install -r requirements.txt
```

### 2. Local Development

```bash
# Authenticate with Azure (az login or set env vars for service principal)
streamlit run cidr_agent_webui.py
```

### 3. Deploy to Azure

- Use the provided `deploy_azure_webapp.sh` for one-command deployment to Azure Web App for Containers.
- Or, push to `main` and let GitHub Actions handle CI/CD.

### 4. Configuration

- The app uses Managed Identity by default in Azure.
- For local/dev, set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` as needed.

### 5. Usage

- Select your Azure subscription in the sidebar.
- Explore the tabs:
  - **Used CIDRs:** View all VNets/subnets and their CIDRs.
  - **Free Up Suggestions:** Find unused VNets and subnets with 0 IPs used.
  - **Suggest CIDR:** Get optimal CIDR blocks for new VNets/subnets.

## 🛡️ Security

- No credentials are stored in the codebase.
- Uses Azure Managed Identity or Service Principal via GitHub Secrets.
- All API calls are read-only (Reader role).

## 📝 Customization

- Edit `.streamlit/config.toml` for theme tweaks.
- Update `cidr_agent_webui.py` for custom logic or integrations.

## 🧪 Testing

- Use `test_freeup_ips.py` to create and clean up test VNets/subnets for demo and validation.

## 🤝 Contributing

Pull requests and issues are welcome!  
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License

---

## 📢 Blog/Announcement Example

> **Introducing Azure CIDR Agent:**  
> A modern, interactive dashboard to visualize, optimize, and reclaim your Azure IP space.  
> No more wasted CIDRs or subnet sprawl—see everything, act instantly, and deploy with confidence.  
> Try it now on [Azure Web App](https://cidragent-webapp.azurewebsites.net) or run locally in minutes! 
