import java.util.*;
import java.io.*;
import edu.stanford.nlp.pipeline.*;
import edu.stanford.nlp.util.*;
import edu.stanford.nlp.ling.*;
import edu.stanford.nlp.ling.CoreAnnotations.*;
// import org.json.*;

public class pipe {

	private static StanfordCoreNLP pipeline;
	private static boolean shortStyle;

	public static void main(String[] args) throws Exception {	    

		Properties props = StringUtils.argsToProperties(args);
		// System.out.println(props.toString());
		props.list(System.err);
		System.err.println("--- end of listing ---");

		if(props.getProperty("short") != null) {
			// shortStyle = props.getProperty("short");
			shortStyle = props.getProperty("short").equalsIgnoreCase("true");
			props.remove("short");
		}

		boolean single = false;
		if(props.getProperty("single") != null) {
			single = props.getProperty("single").equalsIgnoreCase("true");
			props.remove("single");
		}

		int threads = 1;
		if(props.getProperty("threads") != null) {
			threads = Integer.parseInt(props.getProperty("threads"));
		}

		// props.put("annotators", "tokenize, ssplit, pos, lemma, ner");
		// props.put("tokenize.options", "tokenizeNLs=true,ptb3Escaping=false");
		// props.put("ssplit.eolonly", "true");
		// props.put("ssplit.isOneSentence", "true");
		//// props.put("ner.model", "edu/stanford/nlp/models/ner/english.all.3class.distsim.crf.ser.gz");

		pipeline = new StanfordCoreNLP(props);

		if (pipeline == null) throw new Error("Pipeline not initialized");

		PrintStream out = new PrintStream(System.out, true, "UTF8");
		BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF8"));

		if(single) {
			System.err.println("Will start processing after each newline");
		} else {
			System.err.println("Will start processing after two newlines");
		}
		System.err.println("Empty line to quit");

		System.err.println("Ready");
		
		String s;
		if(single) {
			while ((s = in.readLine()) != null && s.length() != 0) {
				// Analyzes a chunk of text, and returns a list of annotated sentences
				// create an empty Annotation just with the given text
				Annotation annotation = new Annotation(s);
				// run all Annotators on this text
				pipeline.annotate(annotation);
				// output results to JSON format
				outputJSON(annotation);
			}
		} else {
			List<Annotation> annotations = new ArrayList<Annotation>();
			while ((s = in.readLine()) != null) {
				if(s.length() == 0) {
					if(annotations.size() > 0) {
						// process
						pipeline.annotate(annotations, threads);
						outputJSON(annotations);
						annotations.clear();
					} else {
						break;	// quit
					}
				} else {
					annotations.add(new Annotation(s));	// create annotations with input text
				}
			}
		}
		System.err.println("Terminating");
		in.close();
		out.close(); 
	}

	public static void appendAnnotationsJSON(StringBuilder sb, Iterable<Annotation> annotations) {
		boolean first = true;
		for (Annotation annotation: annotations) {
			if(first) first = false;
			else sb.append(",");
			appendAnnotationJSON(sb, annotation);
		}
	}

	public static void appendAnnotationJSON(StringBuilder sb, Annotation annotation) {
		List<CoreMap> sentences = annotation.get(SentencesAnnotation.class);
		boolean first = true;
		for (CoreMap sentence: sentences) {
			if(first) first = false;
			else sb.append(",");

			sb.append("{\"tokens\":[");

			// traversing the words in the current sentence
			// a CoreLabel is a CoreMap with additional token-specific methods
			first = true;
			for (CoreLabel token: sentence.get(TokensAnnotation.class)) {
				if(first) first = false;
				else sb.append(",");

				String word = token.get(TextAnnotation.class);
				String lemma = token.get(LemmaAnnotation.class);  
				String pos = token.get(PartOfSpeechAnnotation.class);
				String ne = token.get(NamedEntityTagAnnotation.class);  
				word = word.replace("\\", "\\\\").replace("\"", "\\\"");
				lemma = lemma.replace("\\", "\\\\").replace("\"", "\\\"");

				sb.append(String.format(
					"{\"text\":\"%s\"%s,\"pos\":\"%s\"",
					word,
					shortStyle && lemma.equals(word) ? "" : String.format(",\"lemma\":\"%s\"", lemma),
					pos)
				);
				if(!ne.equalsIgnoreCase("O"))
					sb.append(String.format(",\"ne\":\"%s\"", ne));
				sb.append("}");
			}
			sb.append("]");
			// if(!shortStyle)
				sb.append(",\"text\":\"").append(sentence.toString().replace("\\", "\\\\").replace("\"", "\\\"").replace("\t", "\\t")).append("\"");
			sb.append("}");
			first = false;
		}
	}

	public static void outputJSON(Annotation annotation) {
		StringBuilder sb = new StringBuilder();
		sb.append("[");
		appendAnnotationJSON(sb, annotation);
		sb.append("]");
		System.out.print(sb.toString());
	}

	public static void outputJSON(List<Annotation> annotations) {
		StringBuilder sb = new StringBuilder();
		sb.append("[");
		appendAnnotationsJSON(sb, annotations);
		sb.append("]");
		System.out.println(sb.toString());
	}
}
