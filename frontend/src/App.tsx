import ControlPanel from "./components/controlPanel";
import OCROutputs from "./components/OCROutputs";
import { useOCRStore } from "./store/useOCRStore";

function App() {
	// Use global state for table data
	const patientList = useOCRStore((s) => s.patientList);
	const ocrResponse = useOCRStore((s) => s.ocrResponse);
	const sideTableData = ocrResponse?.finalResult
		? [ocrResponse.finalResult]
		: [];

	return (
		<div className="main-container">
			<div className="outputs-area">
				<OCROutputs mainTableData={patientList} sideTableData={sideTableData} />
			</div>
			<ControlPanel />
		</div>
	);
}

export default App;
