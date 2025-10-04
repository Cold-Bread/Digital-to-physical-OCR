import { useRef, useState } from "react";
import { useOCRStore } from "../store/useOCRStore";
import { BackendResponse, BoxResponse } from "../types/Types";
import ImagePopup from "./ImagePopup";

// API endpoints configuration
const API_BASE_URL = "http://localhost:8000";
const API_ENDPOINTS = {
	BOX: (boxNumber: string) => `${API_BASE_URL}/box/${boxNumber}`,
	PROCESS_IMAGE: `${API_BASE_URL}/process-image`,
	UPDATE_RECORDS: `${API_BASE_URL}/update-records`,
};

interface ControlPanelProps {
	selectedFiles: File[];
	onFileAdd: (file: File) => void;
	onFilesClear: () => void;
}

const ControlPanel = ({
	selectedFiles,
	onFileAdd,
	onFilesClear,
}: ControlPanelProps) => {
	const [boxNumber, setBoxNumber] = useState("");
	const [imagePopupOpen, setImagePopupOpen] = useState(false);
	const [useFallback, setUseFallback] = useState(true);
	const fileInputRef = useRef<HTMLInputElement>(null);

	const setOCRResponse = useOCRStore((s) => s.setOCRResponse);
	const setPatientList = useOCRStore((s) => s.setPatientList);
	const setIsLoading = useOCRStore((s) => s.setIsLoading);
	const isLoading = useOCRStore((s) => s.isLoading);
	const undo = useOCRStore((s) => s.undo);
	const undoAll = useOCRStore((s) => s.undoAll);
	const history = useOCRStore((s) => s.history);
	const patientList = useOCRStore((s) => s.patientList);
	const isImageProcessed = useOCRStore((s) => s.isImageProcessed);

	const handleSaveToSheet = async () => {
		if (patientList.length === 0) {
			alert("No records to save");
			return;
		}

		// Confirmation prompt to prevent accidental saves
		const boxNumber = patientList[0]?.box_number || "Unknown";
		const recordCount = patientList.length;
		const confirmMessage = `Are you sure you want to save ${recordCount} record${
			recordCount !== 1 ? "s" : ""
		} to Google Sheets for box ${boxNumber}?\n\nThis action will update the spreadsheet and cannot be easily undone.`;

		if (!window.confirm(confirmMessage)) {
			return; // User cancelled
		}

		setIsLoading(true);
		try {
			// Get the current box number from the first patient
			const currentBoxNumber = patientList[0]?.box_number;

			// Save the records
			const response = await fetch(API_ENDPOINTS.UPDATE_RECORDS, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(patientList),
			});

			if (!response.ok) {
				throw new Error(`Failed to save: ${response.statusText}`);
			}

			// OPTIMIZATION: Use returned data instead of making another API call
			const result = await response.json();
			console.log("✅ Save operation completed!", result);

			if (result.updated_patients) {
				// Backend returned updated data - no need to refresh
				setPatientList(result.updated_patients);
				console.log("📈 Used returned data - skipped refresh API call");

				// Show performance information
				const performanceInfo = result.performance || {};
				const message = `Records saved successfully!${
					performanceInfo.total_time ? ` (${performanceInfo.total_time})` : ""
				}`;
				alert(message);
			} else {
				// Fallback: refresh data if backend doesn't return updated records
				console.log("🔄 Backend didn't return updated data - refreshing...");
				if (currentBoxNumber) {
					const boxRes = await fetch(API_ENDPOINTS.BOX(currentBoxNumber), {
						method: "POST",
						headers: {
							Accept: "application/json",
							"Content-Type": "application/json",
						},
					});

					if (!boxRes.ok) {
						throw new Error(`Failed to refresh box data: ${boxRes.statusText}`);
					}

					const updatedPatients = await boxRes.json();
					setPatientList(updatedPatients);
					alert("Records saved successfully! Data has been refreshed.");
				} else {
					setPatientList([]);
					setOCRResponse(null, "");
					alert("Records saved successfully!");
				}
			}
		} catch (err) {
			const errorMessage =
				err instanceof Error ? err.message : "An unknown error occurred";
			alert(`Error saving records: ${errorMessage}`);
			console.error(err);
		} finally {
			setIsLoading(false);
		}
	};

	const handleGetBox = async () => {
		if (!boxNumber) return;
		setIsLoading(true);

		try {
			console.log("Fetching box data...");
			const boxRes = await fetch(API_ENDPOINTS.BOX(boxNumber), {
				method: "POST",
				headers: {
					Accept: "application/json",
					"Content-Type": "application/json",
				},
			});

			if (!boxRes.ok) {
				throw new Error(`Box search failed: ${boxRes.statusText}`);
			}

			const patients: BoxResponse = await boxRes.json();
			console.log("Received box data:", patients);
			setPatientList(patients);
		} catch (err) {
			const errorMessage =
				err instanceof Error ? err.message : "An unknown error occurred";
			alert(`Error: ${errorMessage}`);
			console.error(err);
			setPatientList([]);
		} finally {
			setIsLoading(false);
		}
	};

	const handleProcessImage = async () => {
		if (selectedFiles.length === 0) return;

		// Check for already processed images
		const alreadyProcessedFiles = selectedFiles.filter((file) =>
			isImageProcessed(file.name)
		);

		if (alreadyProcessedFiles.length > 0) {
			const shouldProceed = window.confirm(
				`${alreadyProcessedFiles.length} image(s) have already been processed. Do you want to process all ${selectedFiles.length} images again? This will add duplicate results to the table.`
			);
			if (!shouldProceed) {
				return;
			}
		}

		console.log(`Processing ${selectedFiles.length} images...`);
		setIsLoading(true);

		try {
			// Process all images sequentially
			for (let i = 0; i < selectedFiles.length; i++) {
				const file = selectedFiles[i];
				console.log(
					`Processing image ${i + 1}/${selectedFiles.length}:`,
					file.name
				);

				// Send image to /process-image
				const formData = new FormData();
				formData.append("file", file);

				// Build URL with query parameters
				const url = new URL(API_ENDPOINTS.PROCESS_IMAGE);
				url.searchParams.append("use_fallback", useFallback.toString());

				const ocrRes = await fetch(url.toString(), {
					method: "POST",
					body: formData,
				});

				if (!ocrRes.ok) {
					throw new Error(
						`OCR processing failed for ${file.name}: ${ocrRes.statusText}`
					);
				}

				const ocrData = await ocrRes.json();
				console.log(`OCR response for ${file.name}:`, ocrData);

				// Backend now returns paddleOCR directly
				const transformedData: BackendResponse = {
					paddleOCR: ocrData.paddleOCR || [],
				};

				// Add results to the store (this accumulates results instead of replacing)
				setOCRResponse(transformedData, file.name);
			}

			console.log(`Successfully processed ${selectedFiles.length} images`);
		} catch (err) {
			const errorMessage =
				err instanceof Error ? err.message : "An unknown error occurred";
			alert(`Error: ${errorMessage}`);
			console.error(err);
		} finally {
			setIsLoading(false);
		}
	};

	const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const files = e.target.files;
		if (files && files.length > 0) {
			const imageFiles = Array.from(files).filter((file) =>
				file.type.startsWith("image/")
			);

			if (imageFiles.length === 0) {
				alert("No image files found in the selected files");
				e.target.value = "";
				return;
			}

			if (imageFiles.length > 50) {
				alert(
					`Too many images selected (${imageFiles.length}). Maximum allowed is 50 images.`
				);
				e.target.value = "";
				return;
			}

			// Clear previous files first when selecting new images
			onFilesClear();

			// Add all image files
			imageFiles.forEach((file) => onFileAdd(file));

			if (imageFiles.length < files.length) {
				alert(
					`Added ${imageFiles.length} image files. ${
						files.length - imageFiles.length
					} non-image files were skipped.`
				);
			}
		}
	};

	return (
		<div className="control-panel-main">
			<div className="control-panel-center">
				<input
					type="text"
					className="text-input"
					placeholder="Enter Box Number (e.g., TCBOX77)"
					value={boxNumber}
					onChange={(e) => setBoxNumber(e.target.value.toUpperCase())}
					disabled={isLoading}
				/>
				<button
					className="control-panel-button"
					onClick={handleGetBox}
					disabled={!boxNumber || isLoading}
				>
					{isLoading ? "Loading..." : "Get Box"}
				</button>
				<input
					type="file"
					accept="image/*"
					ref={fileInputRef}
					style={{ display: "none" }}
					onChange={handleFileChange}
					disabled={isLoading}
					multiple
				/>
				<button
					className="control-panel-button"
					onClick={() => fileInputRef.current?.click()}
					disabled={isLoading}
					title={
						selectedFiles.length > 0
							? `${selectedFiles.length} image${
									selectedFiles.length !== 1 ? "s" : ""
							  } selected. Click to select new images (will replace current selection).`
							: "Click to select multiple images"
					}
				>
					{selectedFiles.length === 0
						? "Select Images"
						: `${selectedFiles.length} Images Selected`}
				</button>
				<button
					className="control-panel-button"
					onClick={handleProcessImage}
					disabled={selectedFiles.length === 0 || isLoading}
				>
					{isLoading
						? "Processing Images..."
						: selectedFiles.length === 1
						? "Process Image"
						: `Process ${selectedFiles.length} Images`}
				</button>
				<div className="control-panel-option">
					<label>
						<input
							type="checkbox"
							checked={useFallback}
							onChange={(e) => setUseFallback(e.target.checked)}
							disabled={isLoading}
						/>
						<span>Use fallback model if custom model results are poor</span>
					</label>
				</div>
				<div className="divider"></div>
				<button
					className="control-panel-button secondary"
					onClick={undo}
					disabled={isLoading || history.length <= 1}
				>
					Undo
				</button>
				<button
					className="control-panel-button secondary"
					onClick={undoAll}
					disabled={isLoading || history.length <= 1}
				>
					Undo All
				</button>
				<div className="divider"></div>
				<button
					className="control-panel-button primary"
					onClick={handleSaveToSheet}
					disabled={isLoading || patientList.length === 0}
				>
					Save to Sheet
				</button>
			</div>
			<div className="image-controls-group">
				{selectedFiles.length > 0 && (
					<button
						className="control-panel-button secondary"
						onClick={onFilesClear}
						disabled={isLoading}
						title="Clear all selected images"
					>
						Clear Images
					</button>
				)}
				<button
					className="image-popup-button"
					onClick={() => setImagePopupOpen(true)}
					disabled={selectedFiles.length === 0 || isLoading || imagePopupOpen}
				>
					View Images
				</button>
			</div>
			<ImagePopup
				files={selectedFiles}
				open={imagePopupOpen}
				onClose={() => setImagePopupOpen(false)}
				anchorRight={true}
			/>
		</div>
	);
};

export default ControlPanel;
