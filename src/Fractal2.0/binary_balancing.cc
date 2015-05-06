#include "libs.hh"
#include "classes.hh"
#include "headers.hh"
namespace FractalSpace
{
  void binary_balancing(Fractal_Memory* PFM,vector <double>& numbers,double minimum,
			int Nodes,int length,vector <double>& targets,vector <int>& lowers,vector <int>& uppers)
  {
    int too_few=3;
    double VOLMAX=512.0;
    int rank=PFM->p_mess->FractalRank;
    static int COUNTS=0;
    srand(5700+rank);
    double ANodes=Nodes;
    double Alength=length;
    double sum_total=std::accumulate(numbers.begin(),numbers.end(),0.0);
    //    double aver=sum_total/length;
    vector <double>snumbers(length+1);
    minimum=1.0e-10;
    if(!PFM->periodic)
      minimum+=sum_total/Alength/(pow(VOLMAX,1.0/3.0)-1.0);
    snumbers[0]=0.0;
    for(int L=1;L<=length;L++)
      {
	snumbers[L]=snumbers[L-1]+numbers[L-1]+minimum;
	//	cerr << " RANK" << rank << " " << L << " " << numbers[L-1] << " " << snumbers[L] << " " << minimum <<
	//	" " << sum_total << "\n";
      }
    lowers[0]=0;
    sum_total=snumbers[length];
    snumbers.resize(length);
    for(int N=1;N<Nodes;N++)
      {
	//	double aN=N;
	double target=sum_total*targets[N];
	lowers[N]=std::lower_bound(snumbers.begin(),snumbers.end(),target)-snumbers.begin();
	uppers[N-1]=lowers[N];
	//	cerr << " SEARCH" << rank << " " << Nodes << " " << N << " " << target << " " << sum_total << " " << lowers[N] << "\n";
      }
    uppers[Nodes-1]=length-1;
    bool spreading=false;
    bool narrow=true;
    int counterS=0;
    int flip0=0;
    int flip1=0;
    while(narrow)
      {
	narrow=false;
	for(int N=0;N<Nodes;N++)
	  {
	    int many=uppers[N]-lowers[N];
	    if(many < too_few)
	      {
		//		cerr << " NARROW " << rank << " " << Nodes << " "  << N << " " << lowers[N] << " " << many << " ";
		spreading=true;
		narrow=true;
		int flip=(rand()/8) % 2;
		if(flip == 0)
		  {
		    if(N > 0)
		      {
			lowers[N]--;
			uppers[N-1]--;
			//			cerr << "A";
		      }
		    else
		      {
			lowers[1]++;
			uppers[0]++;
			//			cerr << "B";
		      }
		    flip0++;
		  }
		else
		  {
		    if(N < Nodes-1)
		      {
			lowers[N+1]++;
			uppers[N]++;
			//			cerr << "C";
		      }
		    else
		      {
			lowers[Nodes-1]--;
			uppers[Nodes-2]--;
			//			cerr << "D";
		      }
		    flip1++;
		  }
		//		cerr << "\n";
	      }
	  }
	counterS++;
	narrow=narrow && counterS < 1000;
      }
    bool narrowing=false;
    bool toomany=true;
    int counterN=0;
    while(toomany)
      {
	toomany=false;
	double sumt=0.0;
	for(int N=0;N<Nodes;N++)
	  {
	    int lower=max(lowers[N]-2,0);
	    int upper=min(uppers[N]+1,length-1);
	    sumt+=snumbers[upper]-snumbers[lower];
	  }
	double average=sumt/ANodes;
	double maxy=-1.0;
	int labely=-1;
	for(int N=0;N<Nodes;N++)
	  {
	    if(uppers[N]-lowers[N] < too_few)
	      continue;
	    int lower=max(lowers[N]-2,0);
	    int upper=min(uppers[N]+1,length-1);
	    double howmany=snumbers[upper]-snumbers[lower];
	    if(howmany > maxy)
	      {
		maxy=howmany;
		labely=N;
	      }
	  }
	toomany=maxy > 1.3*average;
	if(!toomany)
	  break;
	narrowing=true;
	int flip=(rand()/8) % 2;
	if(flip == 0)
	  {
	    if(labely > 0)
	      {
		lowers[labely]++;
		uppers[labely-1]++;
	      }
	    else
	      {
		lowers[1]--;
		uppers[0]--;
	      }
	  }
	else
	  {
	    if(labely < Nodes-1)
	      {
		lowers[labely+1]--;
		uppers[labely]--;
	      }
	    else
	      {
		lowers[Nodes-1]++;
		uppers[Nodes-2]++;
	      }
	  }
	counterN++;
	toomany=toomany && counterN < 1000;
      }
//     for(int N=0;N<Nodes;N++)
//       cerr << " FINISHED "  << rank << " " << Nodes << " " << N << " " << lowers[N] << " " << uppers[N] << "\n";
//     if(spreading || narrowing)
//       {
// 	cerr << " BINARY "  << rank << " " << Nodes << " " << COUNTS << " " << spreading << " " << counterS << " " ;
// 	cerr << flip0 << " " << flip1 << " ";
// 	cerr << narrowing << " " << counterN << "\n";
//       }
    COUNTS++;
  }
}
