import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import Header from "./Component/header";
import Main from "./Component/main";
import AnalysisLoading from "./Component/AnalysisLoading";
import Result from "./Component/Result"; 
import Wardrobe from "./Component/Wardrobe";
import EvalPage from "./Component/EvalPage";

function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<Main />} />
        <Route path="/analysis" element={<AnalysisLoading />} />
        <Route path="/result" element={<Result />} />
        <Route path="/wardrobe" element={<Wardrobe />} />
        <Route path="/eval" element={<EvalPage apiBase="" />} />
      </Routes>
    </BrowserRouter>
  );
}


export default App;
