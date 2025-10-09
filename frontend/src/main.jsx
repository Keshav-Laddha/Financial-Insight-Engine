// main.jsx: This is the application entry point. It's the first file that runs. 
// Its job is to "mount" your App.jsx component into the index.html file. You won't touch this often.


import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
