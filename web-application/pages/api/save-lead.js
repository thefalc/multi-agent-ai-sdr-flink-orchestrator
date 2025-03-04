const { MongoClient, ObjectId } = require("mongodb");

require('dotenv').config();

const uri = process.env.MONGODB_URI;
const client = new MongoClient(uri);

async function saveLead(leadData) {
  try {
    await client.connect();
    
    const database = client.db("stratusdb");
    const collection = database.collection("leads");

    const result = await collection.insertOne(leadData);
    return result;
  } catch (error) {
    console.error("Error saving lead:", error);
    throw error;
  } finally {
    await client.close();
  }
}

export default async function handler(req, res) {
  if (req.method === "POST") {
    try {
      const { name, email, jobTitle, company, projectDescription, companyWebsite, leadSource } = req.body;
      
      const leadData = {
        name,
        email,
        jobTitle,
        company,
        projectDescription,
        companyWebsite,
        leadSource,
        createdAt: new Date()
      };

      console.log(leadData);
      
      await saveLead(leadData);
      
      res.status(200).json({ ok: true, message: "Lead saved successfully" });
    } catch (error) {
      res.status(500).json({ ok: false, message: "Error saving lead" });
    }
  } else {
    res.setHeader("Allow", ["POST"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}