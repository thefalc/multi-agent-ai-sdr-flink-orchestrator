import { useEffect, useState } from "react";
import Layout from "../components/Layout";

const Home = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    jobTitle: "",
    company: "",
    projectDescription: "",
    companyWebsite: "",
    leadSource: "Demo Request",
  });
  
  const leadSources = [
    "Demo Request",
    "Whitepaper Download - Optimizing Multi-Cloud Data Warehousing with AI",
    "Webinar Attendance - Real-Time Analytics & AI: The Future of Data Infrastructure",
    "Case Study Engagement - How Acme Corp Reduced Query Costs by 50% Using StratusAI Warehouse",
    "Newsletter Signup - Subscribed to StratusDB's Data Insights Newsletter, showing ongoing interest in AI-driven data solutions",
  ];

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch("/api/save-lead", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });
    if (response.ok) {
      alert("Lead captured successfully!");
      setFormData({
        name: "",
        email: "",
        jobTitle: "",
        company: "",
        projectDescription: "",
        companyWebsite: "",
        leadSource: "Demo Request",
      });
    } else {
      alert("Failed to capture lead. Please try again.");
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <h1 className="text-center mb-4">Lead Capture Form</h1>
          <form onSubmit={handleSubmit} className="card p-4 shadow">
            <div className="mb-3">
              <label className="form-label">Full Name</label>
              <input 
                type="text" 
                name="name" 
                value={formData.name} 
                onChange={handleChange} 
                required 
                className="form-control"
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Email</label>
              <input 
                type="email" 
                name="email" 
                value={formData.email} 
                onChange={handleChange} 
                required 
                className="form-control"
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Job Title</label>
              <input 
                type="text" 
                name="jobTitle" 
                value={formData.jobTitle} 
                onChange={handleChange} 
                required 
                className="form-control"
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Company</label>
              <input 
                type="text" 
                name="company" 
                value={formData.company} 
                onChange={handleChange} 
                required 
                className="form-control"
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Company Website</label>
              <input 
                type="url" 
                name="companyWebsite" 
                value={formData.companyWebsite} 
                onChange={handleChange} 
                required 
                className="form-control"
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Project Description</label>
              <textarea 
                name="projectDescription" 
                value={formData.projectDescription} 
                onChange={handleChange} 
                required 
                className="form-control"
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Lead Source</label>
              <select 
                name="leadSource" 
                value={formData.leadSource} 
                onChange={handleChange} 
                className="form-select"
              >
                {leadSources.map((source, index) => (
                  <option key={index} value={source}>{source}</option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn btn-primary w-100">
              Submit
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function StratusDBApp() {
  return (
    <Layout title="StratusDB">
      <Home />
    </Layout>
  );
}
