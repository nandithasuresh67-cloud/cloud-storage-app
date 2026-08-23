import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Shared from "./pages/Shared";
import Starred from "./pages/Starred";
import Trash from "./pages/Trash";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/shared" element={<Shared />} />
        <Route path="/starred" element={<Starred />} />
        <Route path="/trash" element={<Trash />} />
      </Routes>
    </Layout>
  );
}
