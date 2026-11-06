/**
 * Helper to download files to client machine
 */
export function downloadFile(content, fileName, contentType) {
  const a = document.createElement('a');
  const file = new Blob([content], { type: contentType });
  a.href = URL.createObjectURL(file);
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(a.href);
}

/**
 * Generates an aggregated batch execution summary text report
 */
export function generateAggregatedTextReport(items) {
  let report = `DOCTOR PRESCRIPTION OCR SYSTEM - BATCH PROCESSING SUMMARY REPORT\n`;
  report += `Generated at: ${new Date().toLocaleString()}\n`;
  report += `========================================================================\n\n`;

  items.forEach((item, idx) => {
    report += `${idx + 1}. FILE: ${item.filename} (Status: ${item.status.toUpperCase()})\n`;
    report += `------------------------------------------------------------------------\n`;
    
    if (item.status === 'success' && item.result) {
      const res = item.result;
      report += `Patient: ${res.extracted_fields?.patient_name || 'N/A'}\n`;
      report += `Age: ${res.extracted_fields?.patient_age || 'N/A'}\n`;
      report += `Physician: ${res.extracted_fields?.doctor_name || 'N/A'}\n`;
      report += `Diagnosis: ${res.extracted_fields?.diagnosis || 'N/A'}\n`;
      report += `Notes: ${res.extracted_fields?.notes || 'N/A'}\n\n`;
      report += `Medicines List:\n`;
      
      const meds = res.extracted_fields?.medicines || [];
      if (meds.length === 0) {
        report += `  - No medications found.\n`;
      } else {
        meds.forEach((med, mIdx) => {
          report += `  [${mIdx + 1}] Name: ${med.name || 'N/A'} | Dosage: ${med.dosage || 'N/A'} | Freq: ${med.frequency || 'N/A'} | Dur: ${med.duration || 'N/A'}\n`;
        });
      }
    } else if (item.status === 'failed') {
      report += `Error: ${item.error || 'Failed to process file'}\n`;
    }
    
    report += `\n========================================================================\n\n`;
  });

  return report;
}

/**
 * Format OCR single result into structured text report
 */
export function formatSingleResultReport(res, filename) {
  let report = `DOCTOR PRESCRIPTION OCR REPORT\n`;
  report += `File: ${filename}\n`;
  report += `Processed: ${new Date().toLocaleString()}\n`;
  report += `========================================================================\n\n`;

  report += `EXTRACTED ENTITIES:\n`;
  report += `------------------------------------------------------------------------\n`;
  report += `Patient Name  : ${res.extracted_fields?.patient_name || 'N/A'}\n`;
  report += `Patient Age   : ${res.extracted_fields?.patient_age || 'N/A'}\n`;
  report += `Date          : ${res.extracted_fields?.date || 'N/A'}\n`;
  report += `Physician     : ${res.extracted_fields?.doctor_name || 'N/A'}\n`;
  report += `Diagnosis     : ${res.extracted_fields?.diagnosis || 'N/A'}\n`;
  report += `Notes/Usage   : ${res.extracted_fields?.notes || 'N/A'}\n\n`;

  report += `MEDICATIONS:\n`;
  report += `------------------------------------------------------------------------\n`;
  const meds = res.extracted_fields?.medicines || [];
  if (meds.length === 0) {
    report += `- No medicines identified.\n`;
  } else {
    meds.forEach((med, idx) => {
      report += `[${idx + 1}] ${med.name || 'N/A'}\n`;
      report += `    Dosage   : ${med.dosage || 'N/A'}\n`;
      report += `    Frequency: ${med.frequency || 'N/A'}\n`;
      report += `    Duration : ${med.duration || 'N/A'}\n`;
    });
  }

  report += `\nPIPELINE STATISTICS:\n`;
  report += `------------------------------------------------------------------------\n`;
  report += `OCR Recognition Confidence : ${Math.round(res.confidence?.ocr || 0)}%\n`;
  report += `Preprocessing Quality Score: ${Math.round(res.confidence?.preprocessing || 0)}%\n`;
  report += `Engine Utilized            : ${res.ocr?.engine_used || 'Fallback'}\n`;
  
  return report;
}
