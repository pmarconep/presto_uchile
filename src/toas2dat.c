#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "toas2dat_cmd.h"

#define WORKLEN 65536
#define SECPERDAY 86400
#define MAXREAD 32768
/* #define DEBUG */

#ifdef USEDMALLOC
#include "dmalloc.h"
#endif

/* Define a minimal infodata structure with only the fields we need */
typedef struct mini_infodata {
    long N;              /* Number of bins in the data file */
    double dt;           /* Width of each time series bin (sec) */
    double mjd_i;        /* Integer part of MJD of first data */
    double mjd_f;        /* Fractional part of MJD of first data */
    char name[100];      /* Data file name without suffix */
} infodata;

unsigned long getfilelen(FILE * file, size_t size)
{
    int filenum, rt;
    struct stat buf;

    filenum = fileno(file);
    rt = fstat(filenum, &buf);
    if (rt == -1) {
        perror("\nError in getfilelen()");
        printf("\n");
        exit(-1);
    }
    return (unsigned long) (buf.st_size / size);
}

int compare_doubles(const void *a, const void *b)
/* qsort comparison function for doubles */
{
    const double *da = (const double *) a;
    const double *db = (const double *) b;

    return (*da > *db) - (*da < *db);
}

int read_toas(FILE *infile, double **toas)
/* Read a text file containing ASCII text TOAs. */
/* The number of TOAs read is returned.         */
/* Lines beginning with '#' are ignored.        */
{
    double dtmp;
    char line[80], *sptr = NULL;
    int ii=0, numtoa=0;

    /* Read the input file once to count TOAs */
    while (1) {
        sptr = fgets(line, 80, infile);
        if (!feof(infile) && sptr != NULL && sptr[0] != '\n') {
            if (line[0] != '#' && sscanf(line, "%lf", &dtmp) == 1)
                numtoa++;
        } else {
            break;
        }
    }

    *toas = (double *) malloc(sizeof(double) * numtoa);

    /* Rewind and read the TOAs for real */
    rewind(infile);
    while (1) {
        sptr = fgets(line, 80, infile);
        if (!feof(infile) && sptr != NULL && sptr[0] != '\n') {
            if (line[0] != '#' && sscanf(line, "%lf", &(*toas)[ii]) == 1)
                ii++;
        } else {
            break;
        }
    }
    return numtoa;
}

void readinf(infodata *idata, char *filenm)
{
    FILE *infofile;
    char *tmp1, *tmp2, line[200], infofilenm[200];
    
    sprintf(infofilenm, "%s.inf", filenm);
    infofile = fopen(infofilenm, "r");
    if (!infofile) {
        fprintf(stderr, "Error opening information file '%s'.\n", infofilenm);
        exit(-1);
    }
    
    /* Initialize default values */
    idata->N = 0;
    idata->dt = 0.0;
    idata->mjd_i = 0.0;
    idata->mjd_f = 0.0;
    
    /* Read the file line by line */
    while (fgets(line, 200, infofile)) {
        if (line[0] == '#' || line[0] == '\n')
            continue;
        
        if (strncmp(line, " Data file name", 14) == 0) {
            tmp1 = strtok(line, "\"");
            tmp1 = strtok(NULL, "\"");
            strcpy(idata->name, tmp1);
        } else if (strncmp(line, " Number of bins", 14) == 0) {
            sscanf(line, " Number of bins in the time series = %ld", &idata->N);
        } else if (strncmp(line, " Width of each time series", 25) == 0) {
            sscanf(line, " Width of each time series bin (sec) = %lf", &idata->dt);
        } else if (strncmp(line, " Epoch of observation", 20) == 0) {
            sscanf(line, " Epoch of observation (MJD) = %lf", &idata->mjd_i);
            tmp1 = strchr(line, '.');
            if (tmp1) {
                tmp1++;
                tmp2 = tmp1;
                while (*tmp2 >= '0' && *tmp2 <= '9')
                    tmp2++;
                *tmp2 = '\0';
                idata->mjd_f = atof(tmp1);
                idata->mjd_f = idata->mjd_f * pow(10.0, -strlen(tmp1));
                idata->mjd_i = floor(idata->mjd_i);
            }
        }
    }
    fclose(infofile);
}


int main(int argc, char *argv[])
/* Convert a file of TOAs in either text or binary format   */
/* into a floating point time series.  The time series will */
/* have 'cmd->numout' points with each bin of length        */
/* 'cmd->dt' seconds.                                       */
{
    long ii, jj, ntoas, numwrites, numtowrite, numplaced = 0;
    double To, toa, *toaptr, *ddata, lotime, hitime, dtfract, blockt;
    float *fdata;
    FILE *infile, *outfile;
    Cmdline *cmd;

    /* Call usage() if we have no command line arguments */

    if (argc == 1) {
        Program = argv[0];
        usage();
        exit(0);
    }

    /* Parse the command line using the excellent program Clig */

    cmd = parseCmdline(argc, argv);

    /* If -inf flag is used, read parameters from the .inf file */
    if (cmd->inffileP) {
        char *root;
        infodata idata;
        
        // Extract the root filename (remove .inf extension if present)
        root = strdup(cmd->inffile);
        if (strstr(root, ".inf"))
            *(strstr(root, ".inf")) = '\0';
        
        printf("\nReading parameters from '%s.inf':\n", root);
        
        // Read the .inf file
        readinf(&idata, root);
        
        // Set the parameters from the .inf file
        cmd->dt = idata.dt;            // Sample time in seconds
        cmd->numout = idata.N;         // Number of bins
        
        // Only set t0 if not explicitly specified on command line
        if (!cmd->t0P) {
            cmd->t0 = idata.mjd_i + idata.mjd_f;  // Epoch as MJD
            cmd->t0P = 1;
        }
        
        // Mark parameters as set
        cmd->dtP = 1;
        cmd->numoutP = 1;
        
        printf("  Sample time (dt) = %.10g s\n", cmd->dt);
        printf("  Num points (N)   = %ld\n", cmd->numout);
        printf("  Epoch (MJD)      = %.10f\n", cmd->t0);
        
        free(root);
    }

#ifdef DEBUG
    showOptionValues();
#endif

    fprintf(stderr, "\n\n  TOA to Time Series Converter\n");
    fprintf(stderr, "      by Scott M. Ransom\n");
    fprintf(stderr, "        17 October 2000\n\n");

    /* Open our files and read the TOAs */

    printf("\nReading TOAs from '%s'.\n", cmd->argv[0]);
    if (cmd->textP) {           /* Text data */
        infile = fopen(cmd->argv[0], "r");
        ntoas = read_toas(infile, &ddata);
        printf("   Found %ld TOAs.\n", ntoas);
    } else {                    /* Binary data */
        infile = fopen(cmd->argv[0], "rb");
        if (cmd->floatP) {      /* Floating point data */
            ntoas = getfilelen(infile, sizeof(float));
            printf("   Found %ld TOAs.\n", ntoas);
            ddata = (double *) malloc(sizeof(double) * ntoas);
            fdata = (float *) malloc(sizeof(float) * ntoas);
            jj = fread(fdata, sizeof(float), ntoas, infile);
            if (jj != ntoas) {
                printf("\nError reading TOA file.  Only %ld points read.\n\n", jj);
                exit(-1);
            }
            for (jj = 0; jj < ntoas; jj++)
                ddata[jj] = (double) fdata[jj];
            free(fdata);
        } else {                /* Double precision data */
            ntoas = getfilelen(infile, sizeof(double));
            printf("   Found %ld TOAs.\n", ntoas);
            ddata = (double *) malloc(sizeof(double) * ntoas);
            jj = fread(ddata, sizeof(double), ntoas, infile);
            if (jj != ntoas) {
                printf("\nError reading TOA file.  Only %ld points read.\n\n", jj);
                exit(-1);
            }
        }
    }
    fclose(infile);
    outfile = fopen(cmd->outfile, "wb");

    /* Allocate our output array */

    fdata = (float *) malloc(sizeof(float) * WORKLEN);
    printf("\nWriting time series of %ld points of\n", cmd->numout);
    printf("length %f seconds to '%s'.\n\n", cmd->dt, cmd->outfile);

    /* Sort the TOAs */

    qsort(ddata, ntoas, sizeof(double), compare_doubles);

    /* Convert the TOAs to seconds offset from the first TOA */

    if (cmd->t0P)
        To = cmd->t0;
    else
        To = ddata[0];
    if (cmd->secP)
        for (ii = 0; ii < ntoas; ii++)
            ddata[ii] = (ddata[ii] - To);
    else
        for (ii = 0; ii < ntoas; ii++)
            ddata[ii] = (ddata[ii] - To) * SECPERDAY;
    toaptr = ddata;
    toa = *toaptr;

    /* Determine the number of output writes we need */

    numwrites = (cmd->numout % WORKLEN) ?
        cmd->numout / WORKLEN + 1 : cmd->numout / WORKLEN;
    dtfract = 1.0 / cmd->dt;
    blockt = WORKLEN * cmd->dt;

    /* Loop over the number of writes */

    for (ii = 0; ii < numwrites; ii++) {

        /* Determine the beginning and ending times of the output array */

        lotime = ii * blockt;
        hitime = (ii + 1) * blockt;
        numtowrite = ((cmd->numout % WORKLEN) && (ii == (numwrites - 1))) ?
            cmd->numout % WORKLEN : WORKLEN;

        /* Initialize the output data array to all zeros */

        for (jj = 0; jj < WORKLEN; jj++)
            fdata[jj] = 0.0;

        /* Place any TOAs we need to in the current output array */

        while ((toaptr - ddata) < ntoas) {
            if (toa >= hitime)
                break;
            else if (toa >= lotime) {
                fdata[(int) ((toa - lotime) * dtfract)] += 1.0;
                numplaced++;
            }
            toaptr++;
            toa = *toaptr;
        }

        /* Write the output data */

        fwrite(fdata, sizeof(float), numtowrite, outfile);
    }

    /* Cleanup */

    printf("Done.\n   Placed %ld TOAs.\n\n", numplaced);
    fclose(outfile);
    free(fdata);
    free(ddata);
    exit(0);
}
