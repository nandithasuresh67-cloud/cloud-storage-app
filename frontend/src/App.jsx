import { Routes, Route } from "react-router-dom";
import GuestRoute from "./components/GuestRoute";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Shared from "./pages/Shared";
import Signup from "./pages/Signup";
import Starred from "./pages/Starred";
import Trash from "./pages/Trash";

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <GuestRoute>
            <Login />
          </GuestRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <GuestRoute>
            <Signup />
          </GuestRoute>
        }
      />

      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/shared" element={<Shared />} />
                <Route path="/starred" element={<Starred />} />
                <Route path="/trash" element={<Trash />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
