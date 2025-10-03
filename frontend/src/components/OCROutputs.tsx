import { Patient } from "../types/backendResponse";
import { useOCRStore } from "../store/useOCRStore";
import { useMemo } from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import Fuse from "fuse.js";
import "./DataGrid.css";

interface OCROutputsProps {
	boxData: Patient[];
	selectedFile: File | null;
}

const OCROutputs = ({ boxData = [] }: OCROutputsProps) => {
	const allOCRResults = useOCRStore((s) => s.allOCRResults || []);
	const updateOCRResult = useOCRStore((s) => s.updateOCRResult);

	// Debug logging for OCR data structure (only when we have results)
	if (allOCRResults.length > 0) {
		console.log("=== OCR DEBUG INFO ===");
		console.log("Normalized OCR Results:", allOCRResults);
		console.log(
			"Sample names:",
			allOCRResults.slice(0, 3).map((r) => ({
				original: r.name,
				dob: r.dob,
				score: r.score,
			}))
		);
		console.log("=====================");
	}

	const ocrData = useMemo(() => {
		return allOCRResults;
	}, [allOCRResults]);

	// DataGrid columns for Patient (read-only)
	const boxColumns: GridColDef[] = [
		{
			field: "name",
			headerName: "Name",
			flex: 1,
			minWidth: 200,
			maxWidth: 250,
		},
		{ field: "dob", headerName: "DOB", flex: 1, minWidth: 100, maxWidth: 150 },
		{
			field: "year_joined",
			headerName: "Year Joined",
			flex: 1,
			minWidth: 120,
			maxWidth: 150,
			type: "number",
			valueFormatter: (value: number) => value?.toString() || "",
		},
		{
			field: "last_dos",
			headerName: "Last DOS",
			flex: 1,
			minWidth: 120,
			maxWidth: 150,
			type: "number",
			valueFormatter: (value: number) => value?.toString() || "",
		},
		{
			field: "shred_year",
			headerName: "Shred Year",
			flex: 1,
			minWidth: 120,
			maxWidth: 150,
			type: "number",
			valueFormatter: (value: number) => value?.toString() || "",
		},
		{
			field: "is_child_when_joined",
			headerName: "Child When Joined",
			flex: 1,
			minWidth: 160,
			maxWidth: 180,
			type: "boolean",
		},
		{ field: "box_number", headerName: "Box Number", flex: 1, minWidth: 120 },
	];

	const boxRows = boxData.map((row, idx) => ({ ...row, id: idx }));

	// DataGrid columns for OCR (editable)
	const ocrColumns: GridColDef[] = [
		{
			field: "name",
			headerName: "Name",
			flex: 1,
			maxWidth: 250,
			editable: true,
		},
		{ field: "dob", headerName: "DOB", flex: 1, maxWidth: 150, editable: true },
		{
			field: "score",
			headerName: "Confidence",
			flex: 1,
			maxWidth: 150,
			valueFormatter: (value: number) =>
				value ? `${(value * 100).toFixed(1)}%` : "N/A",
		},
	];
	const ocrRows = ocrData.map((row, idx) => ({ ...row, id: idx }));

	// Handle OCR cell edits - the proper way with processRowUpdate
	const handleProcessRowUpdate = (newRow: any, oldRow: any) => {
		console.log("🚀 Processing row update:", { newRow, oldRow });

		const ocrResult = ocrData.find((r) => r.id === newRow.id);
		if (ocrResult && ocrResult.id) {
			// Find what changed
			const changes: any = {};
			Object.keys(newRow).forEach((key) => {
				if (newRow[key] !== oldRow[key]) {
					changes[key] = newRow[key];
				}
			});

			console.log("📋 Changes detected:", changes);
			updateOCRResult(ocrResult.id, changes);
		}

		return newRow; // Return the new row to confirm the update
	};

	// Debug logging for DataGrid rows (only when we have results)
	if (ocrRows.length > 0) {
		console.log("OCR Rows for DataGrid:", ocrRows);
		console.log(
			"OCR Rows sample score values:",
			ocrRows.map((r) => ({
				name: r.name,
				score: r.score,
				scoreType: typeof r.score,
			}))
		);
	}

	// Fuzzy matching setup
	const fuseOptions = {
		keys: ["name", "dob"],
		threshold: 0.3, // adjust for strictness
		includeScore: true,
	};
	const fuse = new Fuse(boxData, fuseOptions);

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

	return (
		<div className="outputs-container-main">
			<div className="box-table-container">
				<h3>Box Records</h3>
				<div className="table-content">
					<DataGrid
						rows={boxRows}
						columns={boxColumns}
						hideFooter
						disableRowSelectionOnClick
						getRowClassName={(params) => getBoxRowClass(params.row)}
						rowHeight={40}
						disableColumnResize={false}
						autoHeight={false}
						disableColumnMenu
					/>
				</div>
			</div>

			<div className="ocr-table-container">
				<h3>OCR Results</h3>
				<div className="table-content">
					<DataGrid
						rows={ocrRows}
						columns={ocrColumns}
						hideFooter
						disableRowSelectionOnClick
						processRowUpdate={handleProcessRowUpdate}
						onProcessRowUpdateError={(error) =>
							console.error("Row update error:", error)
						}
						rowHeight={40}
					/>
				</div>
			</div>
		</div>
	);
};

export default OCROutputs;
