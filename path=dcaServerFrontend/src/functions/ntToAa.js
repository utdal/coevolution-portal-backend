// Build the inverse map once – codon (upper-case) → amino acid
import { genetic_code } from './aaToNt';   // export `genetic_code` from aaToNt.js

const codonToAa = Object.entries(genetic_code)
  .flatMap(([aa, codons]) => codons.map(c => [c, aa]))
  .reduce((acc, [codon, aa]) => {
    acc[codon] = aa;
    return acc;
  }, {});

/**
 * Convert an NT sequence (string) to its AA sequence.
 * Similar contract to aaToNt: returns [aminoAcids, ntFiltered]
 *
 * @param {string} ntSeq - raw nucleotide sequence (spaces/newlines allowed)
 * @returns {[string, string]} [aaSequence, ntFiltered]
 */
export function ntToAa(ntSeq) {
  const cleaned = ntSeq.replace(/\s+/g, '').toUpperCase();
  const ntFiltered = cleaned.replace(/[^ACGT-]/g, '');

  // Split into triplets; skip incomplete codon at end
  const triplets = ntFiltered.match(/.{1,3}/g) || [];
  const aaSeq = triplets
    .filter(codon => codon.length === 3)
    .map(codon => codonToAa[codon] ?? 'X')   // 'X' for unknown/stop
    .join('');

  return [aaSeq, ntFiltered];
} 