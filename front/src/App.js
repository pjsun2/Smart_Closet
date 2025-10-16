import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import Header from "./Component/header";
import Main from "./Component/main";

function App() {
  return (
    <>
      <Header />
      <Main />
      {/* <Routes>
        <Route path="/" element={<Main />} />
      </Routes> */}
    </>
  )

}

export default App;
