package org.opensearch.migrations.errorprone;

import java.util.Set;

import com.google.auto.service.AutoService;
import com.google.errorprone.BugPattern;
import com.google.errorprone.VisitorState;
import com.google.errorprone.bugpatterns.BugChecker;
import com.google.errorprone.matchers.Description;
import com.google.errorprone.util.ASTHelpers;
import com.sun.source.tree.MethodInvocationTree;
import com.sun.tools.javac.code.Symbol;

@AutoService(BugChecker.class)
@BugPattern(
    name = "StructuredLoggingOnly",
    summary = "Only StructuredArguments logging is allowed",
    severity = BugPattern.SeverityLevel.ERROR
)
public class StructuredLoggingChecker extends BugChecker implements BugChecker.MethodInvocationTreeMatcher {

    private static final Set<String> UNSTRUCTURED_LOG_METHODS = Set.of("info", "warn", "debug", "error", "trace");

    @Override
    public Description matchMethodInvocation(MethodInvocationTree tree, VisitorState state) {
        Symbol.MethodSymbol method = ASTHelpers.getSymbol(tree);
        if (method == null) {
            return Description.NO_MATCH;
        }

        var isLogger = method.getEnclosingElement().getQualifiedName().contentEquals("org.slf4j.Logger");
        var isUnstructuredMethod = UNSTRUCTURED_LOG_METHODS.contains(method.getSimpleName().toString());
        if (isLogger && isUnstructuredMethod) {
            var methodName = method.getSimpleName().toString();
            return buildDescription(tree)
                .setMessage("Replace usage of log." + methodName + "(...) with log.at" 
                    + Character.toUpperCase(methodName.charAt(0)) + methodName.substring(1) 
                    + "().setMessage(...).log();")
                .build();
        }
        return Description.NO_MATCH;
    }
}
