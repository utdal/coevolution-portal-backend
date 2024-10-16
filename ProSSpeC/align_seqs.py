from context import align_sequences_with_hmm, combine_easel_TextMSA

sequences = ['RRGLRDYNPISNNICHLTNVSDGASNSLYGVGFGPLILTNRHLFERNNGELVIKSRHGEFVIKNTTQLHLLPIPDRDLLLIRLPKDVPPFPQKLGFRQPEKGERICMVGSFQTKSITSIVSETSTIMPVENSQFWKHWISTKDGQCGSPMVSTKDGKILGLHSLANFQNSINYFAAFPDDFAEKYLHTIEAHEWVKHWKYNTSAISWGSLNIQASQPSGLFKVSKLI',
             'FERNNGELVIKSRHGEFVIKNTTQLHLLPIPDRDLLLIRLPKDVPPFPQKLGFRQPEKGERICMVGSFQ---TSIVSETSTIMPVENSQFWKHWISTKDGQCGS']

#textmsa1, textmsa2 = align_sequences_with_hmm("ProSSpec/PF00863.hmm", "ProSSpeC/peptidaseC4_all_filtered45.fasta", sequences=sequences, headers=["TR|whatever", "TR|Whatever 2"])
#combine_easel_TextMSA(text_msa1=textmsa1, text_msa2=textmsa2)

#textmsa1, textmsa2 = align_sequences_with_hmm("ProSSpec/PF00863.hmm", "ProSSpeC/peptidaseC4_all_filtered45.fasta", sequences=sequences)
#combine_easel_TextMSA(text_msa1=textmsa1, text_msa2=textmsa2)

textmsa1, textmsa2 = align_sequences_with_hmm("ProSSpec/PF00863.hmm", "ProSSpeC/peptidaseC4_all_filtered45.fasta", sequences="ProSSpeC/test_protease_sequences.txt", headers=[">TR|whatever", ">TR|Whatever 2"])
combine_easel_TextMSA(text_msa1=textmsa1, text_msa2=textmsa2)

#sequences = ['SSIELQADTQ', 'SDPAELQA']
#textmsa1, textmsa2 = align_sequences_with_hmm("ProSSpec/manual_sub.hmm", "ProSSpeC/all_substrates_aligned_peptidaseC4.fasta", sequences=sequences)
#combine_easel_TextMSA(text_msa1=textmsa1, text_msa2=textmsa2)