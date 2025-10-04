import { Patient } from "../types/Types";
import { useOCRStore } from "../store/useOCRStore";
import { useMemo } from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { getBoxRowClass, createAlignedOCRTable } from "../utils/matchingUtils";
import "./DataGrid.css";

interface OCROutputsProps {
	boxData: Patient[];
	selectedFiles?: File[];
}

const OCROutputs = ({ boxData = [], selectedFiles = [] }: OCROutputsProps) => {
	const allOCRResults = useOCRStore((s) => s.allOCRResults || []);
	const setPatientList = useOCRStore((s) => s.setPatientList);

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
		console.log("=======================");
	}

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

	// Create enumerated image source mapping based on selectedFiles order
	const imageSourceMapping = useMemo(() => {
		const mapping = new Map<string, string>();

		if (selectedFiles.length > 0) {
			// Use selectedFiles order for consistent numbering with tabs
			selectedFiles.forEach((file, index) => {
				mapping.set(file.name, `${index + 1}`);
			});
		} else {
			// Fallback to unique sources from OCR results
			const uniqueSources = Array.from(
				new Set(allOCRResults.map((r) => r.imageSource).filter(Boolean))
			);
			uniqueSources.forEach((source, index) => {
				mapping.set(source!, `${index + 1}`);
			});
		}

		return mapping;
	}, [allOCRResults, selectedFiles]);

	// NEW: Create aligned OCR table that matches box records table structure
	const alignedOCRData = useMemo(() => {
		return createAlignedOCRTable(boxData, allOCRResults);
	}, [boxData, allOCRResults]);

	// DataGrid columns for Patient (editable - this data goes to Google Sheets)
	const boxColumns: GridColDef[] = [
		{
			field: "name",
			headerName: "Name",
			flex: 1,
			minWidth: 200,
			maxWidth: 250,
			editable: true,
		},
		{
			field: "dob",
			headerName: "DOB",
			flex: 1,
			minWidth: 100,
			maxWidth: 150,
			editable: true,
		},
		{
			field: "year_joined",
			headerName: "Year Joined",
			flex: 1,
			minWidth: 120,
			maxWidth: 150,
			type: "number",
			valueFormatter: (value: number) => value?.toString() || "",
			editable: true,
		},
		{
			field: "last_dos",
			headerName: "Last DOS",
			flex: 1,
			minWidth: 120,
			maxWidth: 150,
			type: "number",
			valueFormatter: (value: number) => value?.toString() || "",
			editable: true,
		},
		{
			field: "shred_year",
			headerName: "Shred Year",
			flex: 1,
			minWidth: 120,
			maxWidth: 150,
			type: "number",
			valueFormatter: (value: number) => value?.toString() || "",
			// shred_year is auto-calculated, not directly editable
		},
		{
			field: "is_child_when_joined",
			headerName: "Child When Joined",
			flex: 1,
			minWidth: 160,
			maxWidth: 180,
			type: "boolean",
			editable: true,
		},
		{
			field: "box_number",
			headerName: "Box Number",
			flex: 1,
			minWidth: 120,
			editable: true,
		},
	];

	const boxRows = boxData.map((row, idx) => ({ ...row, id: idx }));

	// DataGrid columns for OCR (read-only reference data)
	const ocrColumns: GridColDef[] = [
		{
			field: "name",
			headerName: "Name",
			flex: 1,
			minWidth: 200,
			maxWidth: 250,
		},
		{ field: "dob", headerName: "DOB", flex: 1, maxWidth: 150 },
		{
			field: "score",
			headerName: "Confidence",
			flex: 1,
			maxWidth: 150,
			valueFormatter: (value: number) =>
				value ? `${(value * 100).toFixed(1)}%` : "N/A",
		},
		{
			field: "imageSource",
			headerName: "Image",
			flex: 1,
			maxWidth: 120,
			valueFormatter: (value: string) => {
				return value ? imageSourceMapping.get(value) || "Unknown" : "N/A";
			},
		},
	];

	// Create OCR rows from aligned data, handling null entries
	const ocrRows = alignedOCRData.map((row, idx) => {
		if (row === null) {
			// Create empty placeholder row for alignment
			return {
				id: idx,
				name: "",
				dob: "",
				score: undefined,
				imageSource: "",
			};
		}
		return { ...row, id: idx };
	});

	// Calculate shred year based on other fields
	const calculateShredYear = (yearJoined: number, lastDos: number): number => {
		// Business logic: shred year = last DOS + retention period
		// Adjust this calculation based on actual business rules
		const retentionYears = 7; // Example: 7 year retention
		return Math.max(lastDos + retentionYears, yearJoined + retentionYears);
	};

	// Handle Box Records edits - this data goes to Google Sheets
	const handleBoxRowUpdate = (newRow: any, oldRow: any) => {
		console.log("🚀 Processing box record update:", { newRow, oldRow });

		// Auto-calculate shred year if year_joined or last_dos changed
		if (
			newRow.year_joined !== oldRow.year_joined ||
			newRow.last_dos !== oldRow.last_dos
		) {
			newRow.shred_year = calculateShredYear(
				newRow.year_joined || 0,
				newRow.last_dos || 0
			);
			console.log("📅 Auto-calculated shred year:", newRow.shred_year);
		}

		// Update the patient list in the store
		const updatedBoxData = [...boxData];
		const rowIndex = newRow.id; // DataGrid uses array index as id

		if (rowIndex >= 0 && rowIndex < updatedBoxData.length) {
			// Update the specific patient record
			updatedBoxData[rowIndex] = { ...updatedBoxData[rowIndex], ...newRow };
			// Update the store - this will trigger re-render and prepare data for Google Sheets
			setPatientList(updatedBoxData);
			console.log("✅ Updated patient record:", updatedBoxData[rowIndex]);
		}

		return newRow; // Return the new row to confirm the update
	};

	// Debug logging for DataGrid rows (only when we have results)
	if (ocrRows.length > 0) {
		console.log("OCR Rows for DataGrid:", ocrRows);
		console.log(
			"OCR Rows sample score values:",
			ocrRows.map((r: any) => ({
				name: r.name,
				score: r.score,
				scoreType: typeof r.score,
			}))
		);
	}

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
						getRowClassName={(params) =>
							getBoxRowClass(params.row, boxData, allOCRResults)
						}
						processRowUpdate={handleBoxRowUpdate}
						onProcessRowUpdateError={(error) =>
							console.error("Box record update error:", error)
						}
						rowHeight={40}
						disableColumnResize={false}
						autoHeight={true}
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
						rowHeight={40}
						autoHeight={true}
						getRowClassName={(params) => {
							const row = params.row;
							const rowIndex = params.id as number;

							// Empty row (placeholder for alignment)
							if (!row.name && !row.dob) {
								return "ocr-row-empty";
							}

							// Check if this row index corresponds to a patient match
							if (rowIndex < boxData.length) {
								const patient = boxData[rowIndex];
								const matchClass = getBoxRowClass(
									patient,
									boxData,
									allOCRResults
								);

								// If patient has a match, this OCR row should show as matched
								if (matchClass === "row-match") {
									return "ocr-row-matched";
								} else if (matchClass === "row-partial-match") {
									return "ocr-row-partial-matched";
								}
							}

							// Unmatched OCR result
							return "ocr-row-unmatched";
						}}
					/>
				</div>
			</div>
		</div>
	);
};

export default OCROutputs;
