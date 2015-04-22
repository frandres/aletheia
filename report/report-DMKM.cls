% lateX style for master ECD reports (LaTeX2e)
% This file was updated by Julien Velcin the 21st of March 2012

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{reportDMKM}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions
\PassOptionsToPackage{fleqn}{amsmath}
\LoadClass[a4paper,11pt]{article}
\RequirePackage{amsthm}
\RequirePackage{amssymb}
\RequirePackage{amsmath}
%\RequirePackage[french]{babel}
\RequirePackage[latin1]{inputenc}
\RequirePackage{fancyhdr}
\RequirePackage[dvips]{graphicx}
\RequirePackage{epsfig}
\RequirePackage{color}
\RequirePackage{verbatim}
\RequirePackage{vmargin}
\RequirePackage{tabularx}
\RequirePackage{hyperref}

\setmarginsrb{20mm}{25mm}{15mm}{5mm}{0mm}{0mm}{0mm}{5mm}

\newcommand{\tabledesmatieres}
{\ \newpage
  
  \addtolength{\topmargin}{10mm}
  \addtolength{\footskip}{8mm}
  \addtolength{\textheight}{-10mm}
  
  \thispagestyle{empty}
  \ \newpage
  \thispagestyle{empty}
  
  \vspace{15cm}
  \tableofcontents
  
  \ \newpage
  \thispagestyle{empty}
  \ \newpage
  
  \setcounter{page}{1}
}

\newcommand{\references}
{
  \IfFileExists{biblio.bib}
  {
    \newpage
    
    \bibliography{biblio}
    \bibliographystyle{plain}
  }
  {
    \message{ERREUR DMKM : No bibtex File   "biblio.bib"}
  }
}

\newcommand{\appendixECD}
{

  \newpage
  
  \appendix
  
  \begin{flushright}
    {\huge ANNEXES}
  \end{flushright}
  \addcontentsline{toc}{section}{ANNEXES}
  \markboth{\uppercase{Annexes}}{\uppercase{Annexes}}  
  % \renewcommand{\thepage}{\pagenumbering{arabic}}
  \pagenumbering{Roman}
  \setcounter{page}{1}
}

\newcommand{\annexe}[1]
{
  \newpage
  \section{#1}
}

\newcommand{\itemb}{\item[$\bullet$]}

\newcommand\ligne{\hbox{\raisebox{0.4em}{\vrule depth 0pt height 0.4pt width 17cm}}}

\renewcommand{\footnoterule}
{ 
  \vspace{2mm}	
  \kern-3\p@
  \hrule\@width.4\columnwidth
  \kern2.6\p@
}

\newcommand{\Fig}[3]{
  \begin{figure}[!h]
  \begin{center}
  #3
  \end{center}
  \vspace{-4mm}
  \caption{\label{#1}#2}
  \end{figure}
}

\newif\if@logo \@logofalse

\renewcommand{\author}[1] { \def\@author{#1} }
\renewcommand{\date}[1] { \def\@date{#1} }
\newcommand{\tutors}[1] { \def\@tutors{#1} }
\newcommand{\place}[1] { \def\@place{#1} }
\newcommand{\logo}[2] { \@logotrue \def\@logo{#1} \def\@logoSize{#2} }

\renewcommand{\maketitle}
{
  \thispagestyle{empty} 
  \addtolength{\topmargin}{-40pt}
  \begin{center}    
    \begin{list}{}{
        \leftmargin=-10mm
      }
    \item      
      % \begin{tabular}{p{1cm}p{1cm}}
      %   \fbox{
        \begin{tabularx}{\linewidth}{XXXXXX}
          \begin{minipage}{1.0\linewidth}
            \raggedright
            \includegraphics[height=8mm]{img/Logo-upb.pdf}
          \end{minipage}
          &
          \begin{minipage}{1.0\linewidth}
            \centering
            \includegraphics[height=8mm]{img/Logo-UPMC.pdf}
          \end{minipage}
          &
          \begin{minipage}{.8\linewidth}
            \centering
            \includegraphics[height=8mm]{img/logo-ULY2.pdf}
          \end{minipage}
          &
          \begin{minipage}{.8\linewidth}
            \centering
            \includegraphics[height=5mm]{img/Logo-UPC.pdf}
          \end{minipage}
          &
          \begin{minipage}{.8\linewidth}
            \centering
            \includegraphics[height=8mm]{img/Logo-UPN.pdf}
          \end{minipage}
          &
          \begin{minipage}{.8\linewidth}
            \centering
            \includegraphics[height=8mm]{img/Logo-UPO.pdf}
          \end{minipage}
        \end{tabularx}
%      }
    \end{list}
  \end{center}
  %%%%%%%%%%%%% 
  
  \begin{center}
    
    \vspace{2cm}
    
    {\bf \Large Master DMKM Report}
    
    \vspace{3mm}
    \includegraphics[width=3cm]{img/logo-DMKM.pdf}
    % \vspace{3mm}
    
    \vspace{1cm}
    
    {\Huge \@title}
    
    \vspace{1cm}
    
    {\large \@author}
    
    \vspace{1cm}
    
    {\large defended the \@date}
    
  \end{center}
  
  \vspace{3cm}
  
  \begin{tabularx}{.6\linewidth}{rX}
    \large Supervision : & \@tutors \\
    \\
    \large Location : & \@place
    \if@logo
      \begin{center}
        \includegraphics[width=\@logoSize]{\@logo}      
      \end{center}
    \fi
  \end{tabularx}
}

\newenvironment{resume}
{
  {\bf Résumé :}
  \begin{list}{}{
      \leftmargin=15mm
      \rightmargin=15mm}
  \item
    \begin{it}
    }
    {\end{it}
  \end{list}
}

\renewenvironment{abstract}
{
  {\bf Abstract:}
  \begin{list}{}{
      \leftmargin=15mm
      \rightmargin=15mm}
  \item
    \begin{it}
    }
    {\end{it}
  \end{list}
}

