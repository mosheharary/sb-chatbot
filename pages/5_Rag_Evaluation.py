import streamlit as st
from RAGEvaluator import RAGEvaluator
import pandas as pd

from main import get_resources
from main import check_authentication
check_authentication()

st.sidebar.header("Parameters")
prompt_default = st.sidebar.text_area(
    "Default Prompt", 
    value="""You are an expert assistant tasked with answering questions based on provided documents. Follow these guidelines for each response:
1. **Primary Source Check**: Always look for answers in the provided documents first. Use the content of these documents as your primary source, and include relevant information from them in your response. If there are multiple documents, combine the information thoughtfully and concisely.
2. **External Knowledge (Secondary Source)**: If the answer isn’t fully covered in the provided documents, use other information you have access to in order to complete the response. Make it clear when additional information is being included.
3. **Detailed and Structured Responses**: Provide answers in a detailed and organized manner. Use numbered steps to guide the reader through your response logically, highlighting key points and important details. If the question is in the form of multiple choice questions and there are several options to answer , please response only the text of the answer chosen and nothing else .
4. **Clarity and Completeness**: Ensure each response is clear and complete. Avoid unnecessary details but make sure to cover the main aspects of the question thoroughly.
5. **Reference**: Whenever possible, indicate which part of the provided documents your answer is drawn from, using quotes or summaries as needed.
Use this structure to create responses that are thorough, organized, and insightful.

    """,height=150)
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.1)
top_k = st.sidebar.slider("Top K", min_value=1, max_value=10, value=3, step=1)

llm_models = [
            "gpt-4o-mini",
            "gpt-4o",
            "o1-preview"
]

selected_llm_models = st.selectbox(
    "Select OpenAI  Model:",
    options=llm_models,
    index=0,  # Default selection
    help="Choose an OpenAI LLM model from the list. This parameter will take effect when you ask a question."
)

rag = get_resources()['rag']
rag.update_parameters(prompt_default, temperature, top_k)
rag.update_llm_model(selected_llm_models)

qa_pairs = [
    {
'question': 'What is the name of the centralized web access management system that Skybox will no longer support in version 14.0? a) Okta b) SAML c) SiteMinder d) Skybox Cloud Edition',
'answer': 'c) SiteMinder'
    },
    {
'question': 'What is the new URL for providing feedback in the Skybox Web UI? a) https://support.skyboxsecurity.com/s/ b) https://feedback.skyboxsecurity.com/ c) https://support.skyboxsecurity.com/s/productsurvey d) The URL has not changed.',
'answer': 'c) https://support.skyboxsecurity.com/s/productsurvey'
    },
    {
'question': 'Which of the following Change Manager features will NOT be available in version 13.4.110.00 but is planned for inclusion in the 14.1 release? a) Ability to edit and delete records from a CSV with multiple change requests b) Export to CSV from a ticket or a related tab c) Specify a default workflow d) All of the above.',
'answer': 'd) All of the above'
    },
    {
'question': 'Which of the following capabilities was removed from the Java Client in version 13.3? a) Network Map b) Attack Map c) Change Manager d) Access Analyzer',
'answer': 'b) Attack Map'
    },
    {
'question': 'What is the maximum number of objects supported for each dimension of an access rule context in Firewall & Network Assurance and Model Explorer? a) 1,000 b) 10,000 c) 100,000 d) 1,000,000',
'answer': 'c) 100,000'
    },
    {
'question': 'Which external authentication methods are supported by Skybox Admin Console? a) LDAP, SAML, and OpenID b) LDAP, RADIUS, and SAML c) RADIUS, OAuth, and OpenID d) SAML, OpenID, and OAuth',
'answer': 'b) LDAP, RADIUS, and SAML'
    },
    {
'question': 'Where can an administrator define custom ticket statuses in Skybox Admin Console? a) Admin Console > Ticket Status Configuration b) System Settings > Tickets c) Admin Console > System > Settings > Tickets > Custom Ticket Statuses d) Firewall Compliance > Ticket Settings',
'answer': 'c) Admin Console > System > Settings > Tickets > Custom Ticket Statuses'
    },
    {
'question': 'In Skybox, what is the purpose of the "Events and Triggers" section? a) To monitor firewall performance b) To configure automated responses to specific events c) To set user roles and permissions d) To update system licenses',
'answer': 'b) To configure automated responses to specific events'
    },
    {
'question': 'In Skybox Admin Console, where can administrators find configuration options for setting up Single Sign-On (SSO)? a) License Management b) System Monitoring c) User Management > Settings d) Network Assurance',
'answer': 'c) User Management > Settings'
    },
    {
'question': 'What is the maximum number of global trends that can be configured in the Vulnerability Control module of Skybox Admin Console? a) 50 b) 100 c) 75 d) 25',
'answer': 'c) 75'
    },
    {
'question': 'What cloud infrastructure does Skybox Cloud Edition use for its SaaS deployment? a) Google Cloud Platform b) Microsoft Azure c) Amazon Web Services (AWS) d) IBM Cloud',
'answer': 'c) Amazon Web Services (AWS)'
    },
    {
'question': 'Which service type in Skybox Cloud Edition offers a single-tenant environment? a) Enterprise b) Shared c) Public d) Elite',
'answer': 'd) Elite'
    },
    {
'question': 'Skybox Cloud Edition provides service availability of what percentage? a) "98%" b) "99.9%" c) "100%" d) "99.5%"',
'answer': 'b) "99.9%"'
    },
    {
'question': 'Where is Skybox Cloud currently hosted? a) North America, Europe, and Asia-Pacific b) North America and Africa c) Europe only d) North America only',
'answer': 'a) North America, Europe, and Asia-Pacific'
    },
    {
'question': 'What is a primary responsibility of the customer in Skybox Cloud Edition’s shared responsibility model? a) Managing server hardware b) Configuring access permissions c) Running the Skybox Web UI d) Monitoring system health',
'answer': 'b) Configuring access permissions'
    },
    {
'question': 'What are the differences between Skybox Cloud Editions Elite and Enterprise service offerings, and what factors should a customer consider when choosing between them?',
'answer': 'Based on the provided document, here is a detailed comparison of Skybox Cloud Editions Elite and Enterprise services: 1. Key Architectural Differences: Elite Service features a single-tenant architecture with dedicated VPC per customer, uses dedicated virtual machines, is vertically scalable (uses larger EC2 and storage space), and has premium pricing due to dedicated resources. Enterprise Service, on the other hand, uses a multi-tenant environment, has a shared VPC with application and logical level isolation, is horizontally scalable (distributes tenants across multiple VPCs), and is more cost-effective as infrastructure costs are shared across tenants. 2. Performance and Resource Allocation: From the document: "Elite service performance is based on underlying Infrastructure, while Enterprise service performance is based on application (overlay software architecture)." 3. Factors to Consider When Choosing: a) Resource Requirements: Elite is better for customers needing dedicated resources and maximum performance, while Enterprise is suitable for customers comfortable with shared resources. b) Cost Considerations: Elite has higher cost due to dedicated infrastructure, while Enterprise is more affordable due to shared infrastructure costs. c) Isolation Requirements: Elite provides maximum isolation with dedicated VPC, while Enterprise offers logical isolation within shared infrastructure. Reference: This information is primarily drawn from the "Service architecture" section of the document, specifically under "Skybox Cloud Edition Server" where it states: "The two architectures, single tenant and multi-tenant, are correlated to two different commercial service offerings of Skybox Cloud Edition: Elite and Enterprise." The comparison table in the document directly outlines these differences in terms of tenancy, isolation, performance, scalability, and affordability.'
    },
    {
'question': 'What are Skybox Cloud Editions data backup and retention policies, and how does it ensure data security in storage?',
'answer': 'According to the document, Skybox Cloud Edition provides comprehensive data backup services as a complimentary feature requiring no dedicated license. The backup policy includes hourly backups from the last 24 hours, six daily backups, three weekly backups, and five monthly backups. Data restoration can be performed in two ways: either by customers through the UI via a data load window, or by the provider when they detect data corruption or raise a ticket. The system maintains restored data for six months, with weekly validity checks and deletion after the six-month period. For data security, all backups are permanently stored on AWS S3, and data is encrypted on all storage and file system services (data at rest). The system implements strong authorization and authentication mechanisms to prevent unauthorized access to the SaaS service. Backups are stored in a different Amazon Availability Zone (AZ) than the primary customer service, though within the same region. The service backs up all customer data, including information in both Relational (MySQL) and Non-Relational (Elasticsearch) databases, as well as the file system (AWSs EFS). The backup process is comprehensive, covering Model, Tickets, Reports, Configuration, and Users data in bulk. Reference: This information is drawn from the "Data backup and retention" and "Data storage and security" sections of the document, which provide detailed information about backup policies and security measures.'
    },
    {
'question': 'What are the operational responsibilities divided between Skybox and the customer in the Cloud Edition service?',
'answer': 'Based on the document, the operational responsibilities are clearly divided between Skybox Security and the customer. Skybox Securitys responsibilities include server hardware installation and maintenance, server hardware refresh and disposal, installation of Skybox software on the Server including upgrades and patching, server monitoring (both hardware and software), server-side security, server-side data and information privacy, connectivity and consumption of cloud SMTP service for platform notifications and alerts, Server High Availability, data backup, on-prem Collector software upgrades and patching, Collector health monitoring, Managed Skybox Collector monitoring, and license uploads to the system. On the customer side, responsibilities include Collector installation and maintenance (as per health alerts), Collector hardware refresh and disposal (if an Appliance is used), maintaining connectivity between on-prem Collector and SaaS service, Collector-side security according to the shared responsibility model, Collector-side data and information privacy, connectivity with associated network and security devices, collection and data analysis tasks, model health, and configuration and management of Skybox products via the Skybox Admin Console. Additionally, customers must manage user administration (creating users, user groups, custom roles, configuring permissions), policies and triggers, tasks and task sequences, reports for relevant applications, ticket creation, monitoring license usage, and ensuring proper employee training. Reference: This information comes directly from the "Operational responsibilities" section of the document, which clearly outlines the division of responsibilities between Skybox and its customers under "Skybox responsibilities" and "Customer responsibilities" subsections.'
    },
    {
'question': 'What security measures and compliance standards does Skybox Cloud Edition implement to protect customer data?',
'answer': 'According to the document, Skybox Cloud Edition implements comprehensive security measures and maintains several compliance certifications. For access control, they deploy a Web Application Firewall (WAF) to prevent known and zero-day application attacks, offer IP address allowlisting (whitelisting) for Server access, and restrict tenant access to port 443 only. Data protection includes encryption at rest for all storage devices (S3, EBS, EFS), encryption in transit for all public endpoints, with AWS KMS storing encryption keys and certificates managed in AWS Certificates Manager. For database security, MySQL and Elasticsearch containers use TLS and client-based certificates for transit encryption, encrypt data at rest, and operate in network-isolated private subnets within the VPC. Additional security controls include EC2 instances hardened according to CIS Benchmarks, CrowdStrike agent protection for each workload, dedicated VPC environments per customer, and 24/7 SOC team monitoring with SIEM system integration. Regarding compliance, Skybox Cloud Edition adheres to GDPR and CCPA privacy standards, maintains ISO 27017 certification for cloud service security controls, and follows the Shared Responsibility Model defined by the Cloud Security Alliance. The service implements SOC-2 type 2 controls focusing on IT Security, Availability, Confidentiality, Data Integrity, and Privacy for cloud-based services. Reference: This information is sourced from the "Security and service auditing" and "Compliance" sections of the document, which detail the security measures and compliance standards implemented in the service.'
    },
    {
'question': 'What is Skybox Cloud Editions service availability commitment, and what exceptions are included in their downtime calculations?',
'answer': 'According to the document, Skybox Cloud Edition commits to a 99.9% general service availability calculated per calendar month. The service availability calculation excludes several types of downtime: planned downtime occurs during weekly two-hour maintenance windows (Saturday 23:00 PST - Sunday 01:00 PST) and monthly four-hour windows (Saturday 23:00 PST - Sunday 03:00 PST) for software upgrades and maintenance, with advance notification to customers. Unavailability caused by circumstances beyond Skyboxs reasonable control is also excluded, including acts of God, government actions, floods, fires, earthquakes, civil unrest, acts of terror, strikes, computer or telecommunications failures, internet service provider issues, hosting facility problems, and network intrusions or denial of service attacks. Emergency changes, which are modifications to either the application or infrastructure to restore services or prevent disruption, are also excluded from downtime calculations when communicated to customers at least 24 hours in advance, unless immediate resolution of a major incident is required. The service is monitored 24/7 by a network operations center (NOC) using monitoring tools like Datadog to track the status and performance of each tenant, including both Server and Collector monitoring. Reference: This information is drawn from the "Service availability" and "Service monitoring" sections of the document, which outline the specific availability commitments and exclusions in detail.'
    },
    {
'question': 'What are the key updates in Skybox version 13.4.110.00 regarding the Java Client and its transition to the new Web UI?',
'answer': 'The Skybox version 13.4.110.00 release includes significant updates concerning the Java Client and its transition to the Web UI: 1. The Java Client is being gradually phased out in favor of the new Web UI. While the Java Client will still be included with Skybox software distributions until the second half of 2025, some capabilities and screens are being removed. Performance issues and feature deprecations are expected starting with Skybox version 14.0. By September 2025, all support for the Java Client is planned to cease. 2. Skybox has been enhancing its new Web UI, which is intended to fully replace both the legacy Web Client and the Java Client. The Web UI is already robust and continuously gaining new capabilities with each release. 3. Customers are encouraged to transition to the new Web UI. Before migrating, Skybox recommends contacting Customer Care to verify if the current system resources meet the requirements for the Web UI. 4. The "Attack Map" was removed from the Java Client as of version 13.3. The old Network Map in the Web UI was also replaced by the new Network Map introduced in version 13.0. These changes are part of Skyboxs broader effort to modernize its user interface and enhance the overall user experience. For a smooth transition, customers are advised to start using the Web UI and provide feedback through the customer portal or Customer Care.'
    },
    {
'question': 'What is the timeline for the phase-out of the Java Client in Skybox version 13.4.110.00?',
'answer': 'The timeline for the phase-out of the Java Client in Skybox version 13.4.110.00 includes the following: 1. The Java Client will remain part of the Skybox software distributions until the second half of 2025. 2. Starting with Skybox version 14.0, performance issues and feature deprecations related to the Java Client are expected. 3. By September 2025, all support for the Java Client will cease, and customers are encouraged to fully transition to the Web UI before this date. 4. Skybox recommends contacting Customer Care to verify if current system resources meet the requirements for the Web UI to ensure a smooth transition.'
    },
    {
'question': 'What improvements have been introduced in the Web UI in Skybox version 13.4.110.00?',
'answer': 'The Web UI in Skybox version 13.4.110.00 includes several enhancements to improve usability and functionality: 1. The Web UI has been designed to fully replace both the legacy Web Client and the Java Client, offering a modern and intuitive user experience. 2. It continues to gain new capabilities with each release, ensuring feature parity with the legacy clients while introducing improved workflows. 3. The new Network Map, introduced in version 13.0, is now the standard and replaces the old Network Map, providing more efficient network visualization and analysis. 4. Customers are encouraged to adopt the Web UI as their primary interface and provide feedback through the customer portal or Customer Care to help guide further improvements.'
    },
    {
'question': 'What steps should customers take to ensure a smooth transition to the Web UI in Skybox version 13.4.110.00?',
'answer': 'Customers should follow these steps to ensure a smooth transition to the Web UI: 1. Begin familiarizing themselves with the Web UI as it is designed to replace both the legacy Web Client and the Java Client. 2. Verify that their system resources meet the requirements for running the Web UI. Skybox recommends contacting Customer Care to confirm compatibility and address any resource limitations. 3. Review the updated features of the Web UI, such as the improved Network Map and other newly introduced functionalities, to understand its capabilities. 4. Provide feedback about the Web UI through the customer portal or Customer Care to help Skybox refine and enhance the interface further. 5. Plan to transition fully to the Web UI before September 2025, as all support for the Java Client will cease by that time. These steps will help customers maximize the benefits of the Web UI and align with Skybox’s modernization efforts.'
    },
    {
'question': 'What is the purpose of the Access Policy matrix in the Skybox Web UI Admin Console?',
'answer': 'The Access Policy matrix in the Skybox Web UI Admin Console provides a structured way to manage and visualize access policies between source and destination zones. Each cell in the matrix represents a policy section that specifies traffic rules (block or permit) from one source zone to a destination zone. Key features include: 1. Multiple Access Check Groups can be associated with a single cell to enforce specific access rules. 2. A Default Access Check Group can be added to each policy section to define general limitations not covered by specific checks. 3. The matrix format ensures clear representation and management of access policies, reducing errors like duplicate sections or missing rules. 4. Users can edit policies, assign entities to zones, and analyze compliance for firewalls and networks efficiently using the matrix. This tool streamlines access policy management, ensuring consistency and accuracy across the network.'
    },
    {
'question': 'How can users generate a task sequence in the Skybox Web UI Admin Console?',
'answer': 'To generate a task sequence in the Skybox Web UI Admin Console, follow these steps: 1. Navigate to the Tasks Sequence window in the Web UI (Admin-Console  Tasks  Task Sequences). 2. Select the ‘Add Task Sequence’ button. 3. In the new Task Sequence window, give the sequence a name. 4. Add individual tasks to the sequence by pressing on the ‘Add’ button and choosing from the available options, such as discovery tasks, policy checks, or compliance analysis. 5. Arrange the tasks in the desired order of execution to ensure logical and efficient workflow automation. 6. Configure task-specific parameters, such as ‘Firewall Filters’. 6. Save the task sequence and, if required, run it immediately or schedule it for future execution. This feature helps streamline routine operations, ensuring consistency and efficiency in network and security management.'
    },
    {
'question': 'How can administrators view the number of Firewall Assurance licenses available and used, and see the assets attached to the used licenses in the Skybox Web UI Admin Console?',
'answer': 'To view the amount of Firewall Assurance Licenses available and used, and to see the assets attached to the used licenses in the Skybox Web UI Admin Console: 1. Navigate to Admin Console > System > License, Dictionary, and Model. 2. Review the License Information page, which provides details about the total number of Firewall Assurance licenses purchased (listed as "firewallNodes - lic") and the number of licenses currently in use (listed as "firewallNodes - used"). 3. To find details about the assets associated with the used licenses, select the option to view the Associated Assets for the used licenses. This may include the number of network devices or virtual assets managed under these licenses.'
    }
]


def main():

    st.title("Rag Evaluation")
    if st.button("Run Rag Evaluation"):
        rag_evaluator = RAGEvaluator(rag)
        with st.spinner("Evaluating..."):
            results = rag_evaluator.evaluate_qa_pairs(qa_pairs)
        st.write(results)


if __name__ == "__main__":
    main()
