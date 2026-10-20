import { AuthProvider } from './context/AuthContext';
import AppRoutes from './routes/AppRoutes';
import { ThemeProvider } from './context/ThemeProvider';

function App() {
  return (
    <ThemeProvider><AuthProvider><AppRoutes /></AuthProvider></ThemeProvider>
  );
}

export default App;
