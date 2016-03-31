import java.util.*;
import java.io.*;
import edu.stanford.nlp.trees.EnglishGrammaticalStructure;
import edu.stanford.nlp.trees.*;
import edu.stanford.nlp.util.Filter;
import edu.stanford.nlp.util.Filters;
import java.lang.reflect.Method;

public class pipe {

    public static void main(String[] args) throws Exception {	    

		System.err.println("stdin: expects single tree per line, empty line to quit");
		System.err.println("stdout: multiple result lines per single input followed by single empty line, empty output (single empty line only) on error");

		// get hold of private method
		Method dependenciesToString = null;
		Class c = GrammaticalStructure.class;
		for (Method method : c.getDeclaredMethods()) {
			if(method.getName() == "dependenciesToString") {
				method.setAccessible(true);
				dependenciesToString = method;
				break;
			}
		}

		// stdin & stdout
		BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF8"));
		PrintStream out = new PrintStream(System.out, true, "UTF8");

		// key parts from: https://wiki.csc.calpoly.edu/CSC-581-S11-06/browser/trunk/Stanford/stanford-parser-2011-04-20/src/edu/stanford/nlp/trees/EnglishGrammaticalStructure.java?rev=2

		boolean keepPunct = false;
		boolean makeCopulaHead = false;
		boolean conllx = false;

		final Filter<String> puncFilter = keepPunct ? Filters.acceptFilter() : new PennTreebankLanguagePack().punctuationWordRejectFilter();
		final HeadFinder hf = new SemanticHeadFinder( ! makeCopulaHead);
		
		TreeReader tr;
    	String s;
		Tree t;
    	while ((s = in.readLine()) != null && s.length() != 0) {

			tr = new PennTreeReader(new StringReader(s), new LabeledScoredTreeFactory());
			t = tr.readTree();

			if(t == null) {
				System.out.println();	// output empty line on error
				continue;
			}

            GrammaticalStructure gs = new EnglishGrammaticalStructure(t, puncFilter, hf);

			System.out.println(dependenciesToString.invoke(null, gs, gs.typedDependenciesCCprocessed(true), t, conllx, false));
    	}
		System.err.println("Terminating");
	    in.close();
		out.close(); 
	}
}
