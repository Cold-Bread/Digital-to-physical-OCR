import { Patient, OCRResult } from "../types/backendResponse";
import { useOCRStore } from "../store/useOCRStore";
import { useMemo } from "react";
import {
	DataGrid,
	GridColDef,
	GridCellEditStopReasons,
} from "@mui/x-data-grid";
import Fuse from "fuse.js";
import "./DataGrid.css"; // Import MUI DataGrid styling

interface OCROutputsProps {
	boxData: Patient[];
	selectedFile: File | null;
}

const OCROutputs = ({ boxData = [], selectedFile = null }: OCROutputsProps) => {
	const allOCRResults = useOCRStore((s) => s.allOCRResults || []);

	// Fuzzy matching setup
	const fuseOptions = {
		keys: ["name", "dob"],
		threshold: 0.3, // adjust for strictness
		includeScore: true,
	};
	const fuse = new Fuse(boxData, fuseOptions);

	const ocrData = useMemo(
		() => allOCRResults.filter((r) => !r.isPotentialDuplicate || r.isResolved),
		[allOCRResults]
	);

	// DataGrid columns for Patient (read-only)
	const boxColumns: GridColDef[] = [
		{ field: "name", headerName: "Name", flex: 1 },
		{ field: "dob", headerName: "DOB", flex: 1 },
		{
			field: "year_joined",
			headerName: "Year Joined",
			flex: 1,
			type: "number",
		},
		{ field: "last_dos", headerName: "Last DOS", flex: 1, type: "number" },
		{ field: "shred_year", headerName: "Shred Year", flex: 1, type: "number" },
		{
			field: "is_child_when_joined",
			headerName: "Child When Joined",
			flex: 1,
			type: "boolean",
			valueFormatter: (value: boolean) => (value ? "Yes" : "No"),
		},
		{ field: "box_number", headerName: "Box Number", flex: 1 },
	];
	const boxRows = boxData.map((row, idx) => ({ ...row, id: idx }));

	// DataGrid columns for OCR (editable)
	const ocrColumns: GridColDef[] = [
		{ field: "name", headerName: "Name", flex: 1, editable: true },
		{ field: "dob", headerName: "DOB", flex: 1, editable: true },
		{
			field: "score",
			headerName: "Confidence",
			flex: 1,
			valueFormatter: (value: number) =>
				value ? `${(value * 100).toFixed(1)}%` : "N/A",
		},
	];
	const ocrRows = ocrData.map((row, idx) => ({ ...row, id: idx }));

	// Fuzzy match status for each box row
	const getBoxRowClass = (patient: Patient) => {
		if (!patient || !patient.name) return "row-no-match";
		// Find best fuzzy match from OCR results
		let bestScore = 1;
		let bestType: "match" | "partial" | "none" = "none";
		for (const ocr of ocrData) {
			const results = fuse.search({ name: ocr.name ?? "", dob: ocr.dob ?? "" });
			if (results.length > 0) {
				const score = results[0].score ?? 1;
				if (score < 0.15) return "row-match"; // strong match
				if (score < bestScore) {
					bestScore = score;
					bestType = "partial";
				}
			}
		}
		return bestType === "partial" ? "row-partial-match" : "row-no-match";
	};

	// Handle OCR cell edits
	const handleOcrCellEditStop = (params: any) => {
		if (
			params.reason === GridCellEditStopReasons.enterKeyDown ||
			params.reason === GridCellEditStopReasons.cellFocusOut
		) {
			const { id, field, value } = params;
			const index = typeof id === "number" ? id : parseInt(id, 10);
			const updated = { ...ocrData[index] } as OCRResult;
			(updated as any)[field as keyof OCRResult] = value;
			// You may want to update the store here if you want edits to persist
			// For now, just log
			// updateOCRResult(index, updated);
			// If you want to update the store, implement updateOCRResult in your store
		}
	};

	return (
		<div className="outputs-container">
			<div className="main-table-container">
				<h3>Box Records</h3>
				<div style={{ height: 400, width: "100%" }}>
					<DataGrid
						rows={boxRows}
						columns={boxColumns}
						initialState={{
							pagination: { paginationModel: { pageSize: 10, page: 0 } },
						}}
						pageSizeOptions={[10, 25, 50]}
						disableRowSelectionOnClick
						getRowClassName={(params) => getBoxRowClass(params.row)}
						autoHeight
					/>
				</div>
			</div>

			<div className="side-table-container">
				<h3>OCR Results</h3>
				<div style={{ height: 400, width: "100%" }}>
					<DataGrid
						rows={ocrRows}
						columns={ocrColumns}
						initialState={{
							pagination: { paginationModel: { pageSize: 10, page: 0 } },
						}}
						pageSizeOptions={[10, 25, 50]}
						disableRowSelectionOnClick
						onCellEditStop={handleOcrCellEditStop}
						autoHeight
					/>
				</div>
			</div>

			{selectedFile && (
				<div className="image-preview-container">
					<h3>Original Image</h3>
					<img
						src={URL.createObjectURL(selectedFile)}
						alt="Original document"
						className="image-preview"
					/>
				</div>
			)}
		</div>
	);
};

export default OCROutputs;
