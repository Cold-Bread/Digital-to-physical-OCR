import ControlPanel from "./components/controlPanel";
import OCROutputs from "./components/OCROutputs";
import { useState } from "react";

// Placeholder: these would come from API/database/LLM
const mockMainTable = [];
const mockSideTable = [];

function App() {
	// In real app, fetch and set these from backend/LLM
	const [mainTableData, setMainTableData] = useState(mockMainTable);
	const [sideTableData, setSideTableData] = useState(mockSideTable);

	return (
		<div className="main-container">
			<div className="outputs-area">
				<OCROutputs
					mainTableData={mainTableData}
					sideTableData={sideTableData}
				/>
			</div>
			<ControlPanel />
		</div>
	);
}

export default App;
