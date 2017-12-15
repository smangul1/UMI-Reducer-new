import pysam
import sys
import collections
import numpy as np
import random
import csv
import argparse
import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
import matplotlib.pyplot as plt
import pdb


#updated 09/04/2015


def editDistance(s1,s2):
    k=0
    for i in range(0,len(s1)):
        if s1[i]!=s2[i]:
            k+=1
    return k


ap = argparse.ArgumentParser()
ap.add_argument('inbam', help='Mapped reads in bam format')
ap.add_argument('outbam', help='Output file to save reads after collapsing PCR duplicates')
#ap.add_argument('--testN', type=int,
#                help='Run a test using only the first N features, and then '
#                'print out some example feature IDs and their attributes')
ap.add_argument('--m', action='store_true',help='Save multi-mapped reads')
ap.add_argument('--c', action='store_true',help='Change chromosome format')

#cmd https://gist.github.com/daler/ec481811a44b3aa469f3

args = ap.parse_args()





bam=args.inbam
out=args.outbam



chr_list=[]

if args.c:
    for i in range(1,20):
        chr_list.append('chr'+str(i))

    chr_list.append('chrX')
    chr_list.append('chrY')
    chr_list.append('chrM')

else:
    for i in range(1,20):
        chr_list.append(str(i))

    chr_list.append('X')
    chr_list.append('Y')
    chr_list.append('MT')

#print chr

position=[]
position_all_uniq=[]





samfile = pysam.AlignmentFile(bam, "rb" )


dict= {}


mappedReads=[]
numberReadsUnique=0

numberReadsUniquePlusMultiMapped=0

numberReadsUnique_covGreated1=0
numberReadsUnique_filtered=0
readLength=[]
readLength_filtered=[]
before=0
after=0




readSet=set()


bam_header = pysam.Samfile(bam, 'rb').header



outfile = pysam.AlignmentFile(out, "wb", header=bam_header)



print "Open ",bam, "via pysam"



for chr in chr_list:
    dict.clear()
    position[:]=[]

    if args.c:
        print "----------",chr
    else:
        print "----------chr",chr
    for read in samfile.fetch(chr):
        #stores the name of the read in mappedReads
        mappedReads.append(read.query_name)
        if args.m:
            if read.mapq==50:
                numberReadsUnique+=1
            numberReadsUniquePlusMultiMapped+=1
            position.append(read.reference_start)
            #stores length of read
            #returns error with umi-tools example.bam
            readLength.append(len(str(read.query_sequence)))
        else:
            #checks that the mapping quality of the read is equal to 50
            if read.mapq>=10:
                #increments numberReadsUnique
                numberReadsUnique+=1
                #stores the start position of the read
                position.append(read.reference_start)
                #stores the length of the read
                #returns error with umi-tools data
                readLength.append(len(str(read.query_sequence)))


    print "numberReadsUnique: ",numberReadsUnique
    print "numberReadsUniquePlusMultiMapped: ",numberReadsUniquePlusMultiMapped
    print "mappedReads length: ",len(mappedReads)

    #creates dictionary consisting of read position values
    counter_chr=collections.Counter(position)
    position_all_uniq+=position
    print "Number of read positions stored: ", len(position)

    count=0

    print  "Processing", len(counter_chr.items()), "items"

    for key,val in counter_chr.items():
        #print key,val
        if count%10000==1:
            print count
        count+=1

        if val==1:
            for read in samfile.fetch(chr,key,key+1):
                if read.reference_start==key:
                    outfile.write(read)
                    #adds read length to readLength_filtered
                    #returns error with umi-tools data
                    readLength_filtered.append(len(str(read.query_sequence)))
                    numberReadsUnique_filtered+=1
                    readSet.add(read.query_name)






        elif val>1:
            setReads=set()
            setReads.clear()

            if val>1000:
                print val, chr,key
            Read=[]
            Read[:]=[]
            for read in samfile.fetch(chr,key,key+1):
                if read.reference_start==key:
                    Read.append(read)
                    #Identify UMI
                    if args.c:
                        setReads.add(read.query_name.split("_")[1]+"_"+str(read.query_sequence))
                    else:
                        setReads.add(read.query_name.split("_")[3]+"_"+str(read.query_sequence))

        #print key,val





            notsetReads=set()
            notsetReads.clear()
            numberReadsUnique_covGreated1+=len(setReads)
            for i in range(0,val):
                if args.c:
                    if Read[i].query_name.split("_")[1]+"_"+str(Read[i].query_sequence) in setReads and Read[i].query_name.split("_")[1]+"_"+str(Read[i].query_sequence) not in notsetReads:
                            outfile.write(Read[i])
                            numberReadsUnique_filtered+=1
                            readLength_filtered.append(len(str(Read[i].query_sequence)))
                            notsetReads.add(Read[i].query_name.split("_")[1]+"_"+str(Read[i].query_sequence))
                            readSet.add(Read[i].query_name)
                else:
                    if Read[i].query_name.split("_")[3]+"_"+str(Read[i].query_sequence) in setReads and Read[i].query_name.split("_")[3]+"_"+str(Read[i].query_sequence) not in notsetReads:
                            outfile.write(Read[i])
                            numberReadsUnique_filtered+=1
                            readLength_filtered.append(len(str(Read[i].query_sequence)))
                            notsetReads.add(Read[i].query_name.split("_")[3]+"_"+str(Read[i].query_sequence))
                            readSet.add(Read[i].query_name)





outfile.close()



#-----------------------
#statistics


header=[]

header.append('sample')
header.append('Number of mapped reads')
header.append('Number of reads mapped to unique location (UNIQUE reads)')
header.append('Number of reads alligments after collapsing PCR dublicated (an aligment may include several copies of reads) ')
header.append('Number of reads after collapsing PCR dublicated (each read is present once) ')


nr=[]

nr.append(out.split('.')[0])
nr.append(len(set(mappedReads)))
nr.append(numberReadsUnique)


nr.append(numberReadsUnique_filtered)
nr.append(len(readSet))




stat_f=out.split('.')[0]+'.number_of_reads_stat'

with open(stat_f, 'w') as fp:
    a = csv.writer(fp, delimiter=',')
    a.writerow(header)
    a.writerow(nr)




counter=collections.Counter(position_all_uniq)
position_all_uniq=set(position_all_uniq)
print "Number of position with #reads staring >=1", len(position_all_uniq)




#-----------------------
#save as a histogram - counter_length_filtered

x1=[]
xbins1=[]

counter_length_filtered=collections.Counter(readLength_filtered)
for key,val in counter_length_filtered.items():
    #print key,val
    xbins1.append(val)
    x1.append(key)



plot1=out.split('.')[0]+'.readLengthPCRDuplicatesCollapsed.png'
print "save to",plot1



plt.title('Length of reads after collapsing PCR duplicates')

plt.bar(x1,xbins1)
plt.savefig(plot1)



#save as a histogram - counter_length_uniq
x2=[]
xbins2=[]

counter_length=collections.Counter(readLength)
for key,val in counter_length.items():
    #print key,val
    xbins2.append(val)
    x2.append(key)

plot2=out.split('.')[0]+'.readLengthBeforePCRduplicates.png'
print "save to",plot2



plt.title('Length before collapsing PCR duplicates')
plt.bar(x2,xbins2)
plt.savefig(plot2)





print "DONE!"
