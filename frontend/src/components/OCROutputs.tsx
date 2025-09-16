import { Patient, OCRResult } from "../types/backendResponse";
import { useOCRStore } from "../store/useOCRStore";
import React, { useState, useMemo } from "react";

interface OCROutputsProps {
	boxData: Patient[];
	selectedFile: File | null;
}

const OCROutputs = ({ boxData = [], selectedFile = null }: OCROutputsProps) => {
	const updatePatient = useOCRStore((s) => s.updatePatient);
	const allOCRResults = useOCRStore((s) => s.allOCRResults || []);

	const [editingCell, setEditingCell] = useState<{
		index: number;
		field: keyof Patient;
	} | null>(null);
	const [editValue, setEditValue] = useState<string>("");

	const ocrData = useMemo(
		() => allOCRResults.filter((r) => !r.isPotentialDuplicate || r.isResolved),
		[allOCRResults]
	);

	const normalizeName = (name: string): string =>
		String(name || "")
			.toLowerCase()
			.replace(/d\.?o\.?b\.?/i, "")
			.replace(/[^a-z0-9\s]/g, "")
			.trim();

	const normalizeDate = (d: string): string => {
		if (!d) return "";
		const cleaned = String(d)
			.replace(/d\.?o\.?b\.?/i, "")
			.replace(/[^0-9/-]/g, "")
			.trim();
		return cleaned;
	};

	const getMatchStatus = (ocr: OCRResult, patient: Patient) => {
		const oName = normalizeName(ocr.name || "");
		const pName = normalizeName(patient.name || "");
		const nameMatch = oName !== "" && pName !== "" && oName === pName;

		const oDob = normalizeDate(String(ocr.dob || ""));
		const pDob = normalizeDate(String(patient.dob || ""));
		const dobMatch = oDob !== "" && pDob !== "" && oDob === pDob;
		return {
			isMatch: nameMatch && dobMatch,
			isPartialMatch: nameMatch || dobMatch,
			nameMatch,
			dobMatch,
		};
	};

	type MatchResult = {
		isMatch: boolean;
		isPartialMatch: boolean;
		nameMatch: boolean;
		dobMatch: boolean;
	};

	const getBoxRowClass = (patient: Patient) => {
		if (!patient || !patient.name) return "row-no-match";
		let best: MatchResult = {
			isMatch: false,
			isPartialMatch: false,
			nameMatch: false,
			dobMatch: false,
		};
		for (const ocr of ocrData) {
			if (!ocr?.name) continue;
			const status = getMatchStatus(ocr, patient);
			if (status.isMatch) return "row-match";
			if (status.isPartialMatch) best = status;
		}
		return best.isPartialMatch ? "row-partial-match" : "row-no-match";
	};

	const handleEdit = (index: number, field: keyof Patient) => {
		setEditingCell({ index, field });
		setEditValue(String(boxData[index]?.[field] ?? ""));
	};

	const handleSave = () => {
		if (!editingCell) return;
		const { index, field } = editingCell;
		const updated = { ...boxData[index] } as Patient;

		// Assign per-field with explicit types to avoid using `any`
		if (field === "is_child_when_joined") {
			updated.is_child_when_joined = editValue.toLowerCase() === "true";
		} else if (field === "year_joined") {
			const n = parseInt(editValue, 10);
			updated.year_joined = isNaN(n) ? 0 : n;
		} else if (field === "last_dos") {
			const n = parseInt(editValue, 10);
			updated.last_dos = isNaN(n) ? 0 : n;
		} else if (field === "shred_year") {
			const n = parseInt(editValue, 10);
			updated.shred_year = isNaN(n) ? 0 : n;
		} else if (field === "box_number") {
			updated.box_number = editValue;
		} else if (field === "name") {
			updated.name = editValue;
		} else if (field === "dob") {
			updated.dob = editValue;
		} else {
			// Fallback: try to set as string on the updated object (typed cast for edge cases)
			(updated as unknown as Record<string, string>)[String(field)] = editValue;
		}

		updatePatient(index, updated);
		setEditingCell(null);
		setEditValue("");
	};

	const handleKeyDown = (e: React.KeyboardEvent) => {
		if (e.key === "Enter") handleSave();
		if (e.key === "Escape") {
			setEditingCell(null);
			setEditValue("");
		}
	};

	return (
		<div className="outputs-container">
			<div className="main-table-container">
				<h3>Box Records</h3>
				<table className="main-table">
					<thead>
						<tr>
							<th>Name</th>
							<th>DOB</th>
							<th>Year Joined</th>
							<th>Last DOS</th>
							<th>Shred Year</th>
							<th>Child When Joined</th>
							<th>Box Number</th>
						</tr>
					</thead>
					<tbody>
						{boxData.map((patient, i) => (
							<tr key={i} className={getBoxRowClass(patient)}>
								{(Object.keys(patient) as Array<keyof Patient>).map((field) => (
									<td
										key={String(field)}
										onClick={() => handleEdit(i, field)}
										className={
											editingCell?.index === i && editingCell?.field === field
												? "editing"
												: ""
										}
									>
										{editingCell?.index === i &&
										editingCell?.field === field ? (
											<input
												type={
													field === "is_child_when_joined" ? "checkbox" : "text"
												}
												value={editValue}
												onChange={(e) =>
													setEditValue(
														field === "is_child_when_joined"
															? String((e.target as HTMLInputElement).checked)
															: e.target.value
													)
												}
												onKeyDown={handleKeyDown}
												onBlur={handleSave}
												autoFocus
											/>
										) : field === "is_child_when_joined" ? (
											patient[field] ? (
												"Yes"
											) : (
												"No"
											)
										) : (
											String(patient[field] ?? "")
										)}
									</td>
								))}
							</tr>
						))}
					</tbody>
				</table>
			</div>

			<div className="side-table-container">
				<h3>OCR Results</h3>
				<table className="side-table">
					<thead>
						<tr>
							<th>Name</th>
							<th>DOB</th>
							<th>Confidence</th>
							<th>Match Status</th>
						</tr>
					</thead>
					<tbody>
						{ocrData.length === 0
							? boxData.map((_, idx) => (
									<tr key={`empty-${idx}`} className="empty-row">
										<td colSpan={4}></td>
									</tr>
							  ))
							: ocrData.map((ocr, idx) => {
									const bestStatus = boxData.reduce(
										(best, patient) => {
											if (!ocr?.name || !patient?.name) return best;
											const s = getMatchStatus(ocr, patient);
											if (s.isMatch) return s;
											if (s.isPartialMatch && !best.isMatch) return s;
											return best;
										},
										{
											isMatch: false,
											isPartialMatch: false,
											nameMatch: false,
											dobMatch: false,
										}
									);

									const rowClass = bestStatus.isMatch
										? "row-match"
										: bestStatus.isPartialMatch
										? "row-partial-match"
										: "row-no-match";

									return (
										<tr key={`ocr-${idx}`} className={rowClass}>
											<td>{ocr.name}</td>
											<td>{ocr.dob || "N/A"}</td>
											<td>
												{ocr.score ? `${(ocr.score * 100).toFixed(1)}%` : "N/A"}
											</td>
											<td>
												{bestStatus.isMatch
													? "✓"
													: bestStatus.nameMatch
													? "Name Match"
													: bestStatus.dobMatch
													? "DOB Match"
													: "No Match"}
											</td>
										</tr>
									);
							  })}
					</tbody>
				</table>
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
